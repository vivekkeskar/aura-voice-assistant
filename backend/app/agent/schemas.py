from typing import Any, Dict, Optional

from pydantic import BaseModel


class AgentResponseChunk(BaseModel):
    type: str  # "text_chunk", "tool_start", "tool_result", "done", "error"
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None
    tool_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ConversationState(BaseModel):
    state: str  # IDLE, LISTENING, THINKING, USING_TOOL, SPEAKING, ERROR
    message: Optional[str] = None
