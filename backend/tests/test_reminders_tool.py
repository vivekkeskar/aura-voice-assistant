import pytest

from app.tools.reminders import CreateReminderTool, ListRemindersTool


@pytest.mark.asyncio
async def test_reminders_create_and_list(test_db_session):
    create_tool = CreateReminderTool()
    list_tool = ListRemindersTool()

    create_res = await create_tool.execute(
        {"title": "Study Python Async", "datetime_str": "tomorrow at 8 PM"}, session=test_db_session
    )
    assert "error" not in create_res
    assert create_res["title"] == "Study Python Async"
    assert "scheduled_time" in create_res

    list_res = await list_tool.execute({}, session=test_db_session)
    assert "error" not in list_res
    assert list_res["count"] == 1
    assert list_res["reminders"][0]["title"] == "Study Python Async"
