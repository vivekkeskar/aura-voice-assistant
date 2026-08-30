import asyncio
import json
import time
import uuid
from typing import Dict, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agent.agent import aura_agent
from app.database.database import AsyncSessionLocal
from app.database.repository import ConversationRepository
from app.services.tts.tts_service import tts_service
from app.utils.logger import logger
from app.websocket.manager import manager

router = APIRouter()

# Track active execution tasks per conversation for instant cancellation on interruption
active_agent_tasks: Dict[str, asyncio.Task] = {}


@router.websocket("/ws/voice")
async def voice_websocket_endpoint(websocket: WebSocket, conversation_id: Optional[str] = None):
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    await manager.connect(conversation_id, websocket)

    # Initial state greeting
    await manager.send_json(conversation_id, {"type": "connection_established", "conversation_id": conversation_id})
    await manager.send_state(conversation_id, "IDLE")

    try:
        while True:
            raw_msg = await websocket.receive_text()
            try:
                data = json.loads(raw_msg)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            # 1. Handle Interruption Frame
            if msg_type == "interrupt":
                logger.info(f"Received interruption signal from {conversation_id}")
                if conversation_id in active_agent_tasks:
                    task = active_agent_tasks[conversation_id]
                    if not task.done():
                        task.cancel()
                        logger.info(f"Cancelled ongoing agent generation task for {conversation_id}")
                    del active_agent_tasks[conversation_id]

                await manager.send_state(conversation_id, "LISTENING")
                continue

            # 2. Handle Clear Conversation Command
            elif msg_type == "clear_conversation":
                async with AsyncSessionLocal() as db_session:
                    repo = ConversationRepository(db_session)
                    await repo.clear_conversation(conversation_id)
                await manager.send_json(
                    conversation_id, {"type": "conversation_cleared", "conversation_id": conversation_id}
                )
                await manager.send_state(conversation_id, "IDLE")

            # 3. Handle Text Input or Final Audio Transcript
            elif msg_type in ["text_input", "transcript_final"]:
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                logger.info(f"Received input from {conversation_id}: '{user_text}'")

                # Emit final transcript event to client UI
                await manager.send_json(conversation_id, {"type": "transcript_final", "text": user_text})

                # Cancel any previous running task
                if conversation_id in active_agent_tasks:
                    old_task = active_agent_tasks[conversation_id]
                    if not old_task.done():
                        old_task.cancel()

                # Spawn async processing pipeline task
                task = asyncio.create_task(run_voice_pipeline(conversation_id, user_text))
                active_agent_tasks[conversation_id] = task

            elif msg_type == "ping":
                await manager.send_json(conversation_id, {"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(conversation_id)
        if conversation_id in active_agent_tasks:
            active_agent_tasks[conversation_id].cancel()
            del active_agent_tasks[conversation_id]
    except Exception as e:
        logger.error(f"WebSocket error in session {conversation_id}: {e}")
        manager.disconnect(conversation_id)


async def run_voice_pipeline(conversation_id: str, user_text: str):
    """
    Executes the full pipeline and tracks empirical latency metrics:
    State: THINKING -> Agent Reasoning -> (State: USING_TOOL -> Tool execution) -> State: SPEAKING -> Streaming TTS Audio -> State: IDLE
    """
    t_start = time.time()
    t_first_token = None
    t_tool_start = None
    t_tool_duration = 0.0
    t_first_audio = None

    try:
        await manager.send_state(conversation_id, "THINKING")

        async with AsyncSessionLocal() as db_session:
            async for chunk in aura_agent.process_user_request_stream(user_text, conversation_id, db_session):
                await asyncio.sleep(0)  # Check for cancellation

                if chunk.type == "tool_start":
                    t_tool_start = time.time()
                    await manager.send_state(conversation_id, "USING_TOOL")
                    await manager.send_json(
                        conversation_id, {"type": "tool_start", "tool": chunk.tool_name, "params": chunk.tool_params}
                    )

                elif chunk.type == "tool_result":
                    if t_tool_start:
                        t_tool_duration += time.time() - t_tool_start
                    await manager.send_json(
                        conversation_id, {"type": "tool_result", "tool": chunk.tool_name, "result": chunk.tool_result}
                    )

                elif chunk.type == "text_chunk":
                    if t_first_token is None:
                        t_first_token = time.time() - t_start

                    assistant_text = chunk.content or ""
                    if assistant_text:
                        await manager.send_json(
                            conversation_id, {"type": "assistant_text", "text": assistant_text, "is_final": True}
                        )

                        await manager.send_state(conversation_id, "SPEAKING")

                        # Stream TTS Audio Chunks directly over WebSocket
                        t_tts_start = time.time()
                        async for audio_b64 in tts_service.stream_tts_audio_base64(assistant_text):
                            await asyncio.sleep(0)
                            if t_first_audio is None:
                                t_first_audio = time.time() - t_tts_start

                            await manager.send_json(
                                conversation_id, {"type": "audio", "data": audio_b64, "sample_rate": 24000}
                            )

                elif chunk.type == "error":
                    await manager.send_state(conversation_id, "ERROR")
                    await manager.send_json(
                        conversation_id, {"type": "error", "message": chunk.error or "Pipeline error occurred."}
                    )

            await db_session.commit()

        total_latency = time.time() - t_start

        # Emit empirical latency metrics frame
        await manager.send_json(
            conversation_id,
            {
                "type": "metrics",
                "metrics": {
                    "llm_ttft": round(t_first_token or 0, 3),
                    "tool_execution_time": round(t_tool_duration, 3),
                    "tts_first_audio": round(t_first_audio or 0, 3),
                    "total_latency": round(total_latency, 3),
                },
            },
        )

        await manager.send_state(conversation_id, "IDLE")

    except asyncio.CancelledError:
        logger.info(f"Pipeline task for {conversation_id} was interrupted/cancelled.")
        await manager.send_state(conversation_id, "LISTENING")
    except Exception as e:
        logger.error(f"Error running pipeline for {conversation_id}: {e}")
        await manager.send_state(conversation_id, "ERROR")
        await manager.send_json(conversation_id, {"type": "error", "message": f"Pipeline processing failed: {str(e)}"})
