import pytest

from app.agent.agent import aura_agent


@pytest.mark.asyncio
async def test_agent_weather_query(test_db_session):
    chunks = []
    async for chunk in aura_agent.process_user_request_stream(
        "What's the weather in Pune?", "conv_123", test_db_session
    ):
        chunks.append(chunk)

    tool_starts = [c for c in chunks if c.type == "tool_start"]
    text_chunks = [c for c in chunks if c.type == "text_chunk"]

    assert len(tool_starts) >= 1
    assert tool_starts[0].tool_name == "get_weather"
    assert len(text_chunks) >= 1
    assert "pune" in text_chunks[0].content.lower()


@pytest.mark.asyncio
async def test_agent_create_note_query(test_db_session):
    chunks = []
    async for chunk in aura_agent.process_user_request_stream(
        "Create a note saying prepare for interview", "conv_123", test_db_session
    ):
        chunks.append(chunk)

    tool_starts = [c for c in chunks if c.type == "tool_start"]
    text_chunks = [c for c in chunks if c.type == "text_chunk"]

    assert len(tool_starts) >= 1
    assert tool_starts[0].tool_name == "create_note"
    assert len(text_chunks) >= 1
    assert "saved" in text_chunks[0].content.lower() or "note" in text_chunks[0].content.lower()


@pytest.mark.asyncio
async def test_agent_multi_step_query(test_db_session):
    chunks = []
    async for chunk in aura_agent.process_user_request_stream(
        "What's the weather in Mumbai and create a note saying carry an umbrella.", "conv_123", test_db_session
    ):
        chunks.append(chunk)

    tool_starts = [c for c in chunks if c.type == "tool_start"]
    assert len(tool_starts) >= 2
    tool_names = [t.tool_name for t in tool_starts]
    assert "get_weather" in tool_names
    assert "create_note" in tool_names
