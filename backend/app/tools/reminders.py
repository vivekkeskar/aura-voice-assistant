from datetime import datetime, timedelta
from typing import Any, Dict, Optional

import dateparser
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import ReminderRepository
from app.tools.base import BaseTool, tool_registry
from app.utils.logger import logger


class CreateReminderTool(BaseTool):
    name = "create_reminder"
    description = "Create and schedule a new reminder with a title and date/time."
    parameters = {
        "type": "OBJECT",
        "properties": {
            "title": {
                "type": "STRING",
                "description": "What to be reminded about (e.g., 'Study for AI interview', 'Buy groceries').",
            },
            "datetime_str": {
                "type": "STRING",
                "description": "When to trigger the reminder (e.g., 'tomorrow at 8 PM', 'in 2 hours', '2026-08-31 20:00').",
            },
        },
        "required": ["title", "datetime_str"],
    }

    async def execute(self, params: Dict[str, Any], session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        if not session:
            return {"error": "Database session unavailable."}

        title = params.get("title", "").strip()
        datetime_raw = params.get("datetime_str", "").strip()

        if not title:
            return {"error": "Reminder title is required."}
        if not datetime_raw:
            return {"error": "Reminder date/time is required."}

        # Parse date using dateparser
        parsed_dt = dateparser.parse(
            datetime_raw, settings={"PREFER_DATES_FROM": "future", "RELATIVE_BASE": datetime.now()}
        )

        if not parsed_dt:
            # Fallback parsing for standard formats
            try:
                parsed_dt = datetime.fromisoformat(datetime_raw)
            except ValueError:
                parsed_dt = datetime.now() + timedelta(hours=2)

        repo = ReminderRepository(session)
        reminder = await repo.create_reminder(title=title, scheduled_datetime=parsed_dt)

        formatted_time = reminder.scheduled_datetime.strftime("%B %d, %Y at %I:%M %p")
        logger.info(f"Created reminder ID {reminder.id}: {title} for {formatted_time}")

        return {
            "id": reminder.id,
            "title": reminder.title,
            "scheduled_time": formatted_time,
            "status": reminder.status,
            "message": f"Reminder created for '{title}' on {formatted_time}.",
        }


class ListRemindersTool(BaseTool):
    name = "list_reminders"
    description = "List all scheduled reminders."
    parameters = {
        "type": "OBJECT",
        "properties": {
            "status": {"type": "STRING", "description": "Optional filter status: 'pending', 'completed', or 'all'."}
        },
    }

    async def execute(self, params: Dict[str, Any], session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        if not session:
            return {"error": "Database session unavailable."}

        status_filter = params.get("status")
        if status_filter == "all":
            status_filter = None

        repo = ReminderRepository(session)
        reminders = await repo.list_reminders(status_filter=status_filter)

        formatted_list = []
        for r in reminders:
            formatted_list.append(
                {
                    "id": r.id,
                    "title": r.title,
                    "scheduled_time": r.scheduled_datetime.strftime("%B %d, %Y at %I:%M %p"),
                    "status": r.status,
                }
            )

        logger.info(f"Retrieved {len(formatted_list)} reminders.")
        return {"count": len(formatted_list), "reminders": formatted_list}


tool_registry.register(CreateReminderTool())
tool_registry.register(ListRemindersTool())
