import pytest

from app.tools.notes import CreateNoteTool, ListNotesTool


@pytest.mark.asyncio
async def test_notes_tool_create_and_list(test_db_session):
    create_tool = CreateNoteTool()
    list_tool = ListNotesTool()

    # 1. Create note
    create_res = await create_tool.execute({"content": "Prepare for AI interview"}, session=test_db_session)
    assert "error" not in create_res
    assert create_res["content"] == "Prepare for AI interview"
    assert "id" in create_res

    # 2. List notes
    list_res = await list_tool.execute({}, session=test_db_session)
    assert "error" not in list_res
    assert list_res["count"] == 1
    assert list_res["notes"][0]["content"] == "Prepare for AI interview"


@pytest.mark.asyncio
async def test_create_note_empty_content(test_db_session):
    create_tool = CreateNoteTool()
    res = await create_tool.execute({"content": "   "}, session=test_db_session)
    assert "error" in res
