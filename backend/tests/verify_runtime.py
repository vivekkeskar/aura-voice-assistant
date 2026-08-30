import asyncio
import json
import time

import httpx
import websockets

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/voice"


async def run_verification():
    print("==================================================")
    print("1. VERIFYING BACKEND & FRONTEND HTTP ENDPOINTS")
    print("==================================================")
    async with httpx.AsyncClient() as client:
        res_health = await client.get(f"{BASE_URL}/health")
        print(f"Backend /health status: {res_health.status_code} -> {res_health.json()}")

        res_frontend = await client.get("http://localhost:3000")
        print(f"Frontend HTTP status: {res_frontend.status_code}")

    print("\n==================================================")
    print("2. VERIFYING WEBSOCKET CONNECTION & PROTOCOL")
    print("==================================================")
    async with websockets.connect(WS_URL) as ws:
        init_msg = await ws.recv()
        print(f"Received init message: {init_msg}")

        state_msg = await ws.recv()
        print(f"Received initial state: {state_msg}")

        # Send Ping
        await ws.send(json.dumps({"type": "ping"}))
        pong_msg = await ws.recv()
        print(f"Received ping response: {pong_msg}")

    print("\n==================================================")
    print("3. VERIFYING WEATHER TOOL & AGENT ROUTING")
    print("==================================================")
    async with websockets.connect(WS_URL) as ws:
        await ws.recv()  # init
        await ws.recv()  # state

        t0 = time.time()
        await ws.send(json.dumps({"type": "text_input", "text": "What's the weather in Pune?"}))

        received_frames = []
        ttft = None
        first_audio_byte_time = None

        while True:
            try:
                frame_raw = await asyncio.wait_for(ws.recv(), timeout=10.0)
                frame = json.loads(frame_raw)
                received_frames.append(frame)
                frame_type = frame.get("type")
                now = time.time()

                if frame_type == "assistant_text" and ttft is None:
                    ttft = now - t0
                    print(f"  - Time-to-first-token (LLM): {ttft:.3f}s")
                elif frame_type == "audio" and first_audio_byte_time is None:
                    first_audio_byte_time = now - t0
                    print(f"  - Time-to-first-audio-byte (TTS): {first_audio_byte_time:.3f}s")

                print(
                    f"  <- WS Frame: type={frame_type}, value/text={frame.get('value') or frame.get('text') or frame.get('tool')}"
                )

                if frame_type == "state" and frame.get("value") == "IDLE" and len(received_frames) > 3:
                    break
            except asyncio.TimeoutError:
                print("  ! WS Timeout waiting for response")
                break

        total_latency = time.time() - t0
        print(f"  - Total Weather Query Pipeline Latency: {total_latency:.3f}s")

    print("\n==================================================")
    print("4. VERIFYING NOTES PERSISTENCE IN SQLITE")
    print("==================================================")
    async with websockets.connect(WS_URL) as ws:
        await ws.recv()  # init
        await ws.recv()  # state

        await ws.send(json.dumps({"type": "text_input", "text": "Create a note saying prepare for my AI interview."}))

        while True:
            frame_raw = await ws.recv()
            frame = json.loads(frame_raw)
            print(
                f"  [Note Stream] type={frame.get('type')}, val={frame.get('value') or frame.get('text') or frame.get('tool')}, res={frame.get('result')}"
            )
            if frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

    # Verify SQLite REST query
    async with httpx.AsyncClient() as client:
        notes_res = await client.get(f"{BASE_URL}/api/notes")
        notes_data = notes_res.json()
        print(f"SQLite Persisted Notes: {json.dumps(notes_data, indent=2)}")

    print("\n==================================================")
    print("5. VERIFYING REMINDERS PERSISTENCE IN SQLITE")
    print("==================================================")
    async with websockets.connect(WS_URL) as ws:
        await ws.recv()  # init
        await ws.recv()  # state

        await ws.send(json.dumps({"type": "text_input", "text": "Remind me to study tomorrow at 8 PM."}))

        while True:
            frame_raw = await ws.recv()
            frame = json.loads(frame_raw)
            print(
                f"  [Reminder Stream] type={frame.get('type')}, val={frame.get('value') or frame.get('text') or frame.get('tool')}"
            )
            if frame.get("type") == "state" and frame.get("value") == "IDLE":
                break

    # Verify SQLite REST query for reminders
    async with httpx.AsyncClient() as client:
        rems_res = await client.get(f"{BASE_URL}/api/reminders")
        rems_data = rems_res.json()
        print(f"SQLite Persisted Reminders: {json.dumps(rems_data, indent=2)}")

    print("\n==================================================")
    print("6. VERIFYING BARGE-IN / INTERRUPTION CANCELLATION")
    print("==================================================")
    async with websockets.connect(WS_URL) as ws:
        await ws.recv()
        await ws.recv()

        await ws.send(json.dumps({"type": "text_input", "text": "Show my notes and list all my reminders."}))

        while True:
            frame_raw = await ws.recv()
            frame = json.loads(frame_raw)
            print(f"  [Barge-In Pre-State] type={frame.get('type')}, value={frame.get('value')}")
            if frame.get("type") == "state" and frame.get("value") in ["THINKING", "SPEAKING"]:
                break

        print("  -> Emitting user interrupt signal to cancel backend task...")
        await ws.send(json.dumps({"type": "interrupt"}))

        next_frame_raw = await ws.recv()
        next_frame = json.loads(next_frame_raw)
        print(f"  <- Response after interrupt signal: {next_frame}")
        assert next_frame.get("value") == "LISTENING"
        print("  ✓ Barge-In Backend Task Cancellation VERIFIED!")


if __name__ == "__main__":
    asyncio.run(run_verification())
