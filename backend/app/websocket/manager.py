from typing import Dict

from fastapi import WebSocket

from app.utils.logger import logger


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, conversation_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[conversation_id] = websocket
        logger.info(f"WebSocket connected for conversation: {conversation_id}")

    def disconnect(self, conversation_id: str):
        if conversation_id in self.active_connections:
            del self.active_connections[conversation_id]
            logger.info(f"WebSocket disconnected for conversation: {conversation_id}")

    async def send_json(self, conversation_id: str, message: dict):
        ws = self.active_connections.get(conversation_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.error(f"Error sending WS message to {conversation_id}: {e}")

    async def send_state(self, conversation_id: str, state_val: str):
        await self.send_json(conversation_id, {"type": "state", "value": state_val})


manager = ConnectionManager()
