import re
from typing import Any, Dict, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database.repository import NoteRepository
from app.tools.base import BaseTool, tool_registry
from app.utils.logger import logger


def normalize_note_content(raw_text: str) -> str:
    """
    Strips leading trigger phrases (e.g. 'create a note saying', 'make a note that',
    'note this', 'remember this', 'write this down') and surrounding punctuation/quotes,
    preserving exact user-intended sentence content without altering wording or meaning.
    """
    if not raw_text:
        return ""

    text = raw_text.strip()

    # Strip leading/trailing quotes if whole string is wrapped in quotes
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()

    # Regex patterns for common command prefixes
    prefixes = [
        r"^(?:please\s+)?(?:create|make|save|take|add)\s+(?:a\s+)?note\s+(?:saying|that|this|to|about)?[\s:,]*",
        r"^(?:please\s+)?(?:note|remember|write\s*down|jot\s*down)\s+(?:this|that)?[\s:,]*",
    ]

    for pat in prefixes:
        text = re.sub(pat, "", text, flags=re.IGNORECASE).strip()

    # Strip any leading colon, comma, or dash
    text = re.sub(r"^[\s:,.\-\"\']+", "", text).strip()
    # Strip trailing colons or quotes if leftover
    text = text.strip("\"':")

    return text


class CreateNoteTool(BaseTool):
    name = "create_note"
    description = (
        "Create and save a new text note. Extract only the actual note content intended by the user, "
        "stripping away command trigger phrases such as 'create a note saying', 'make a note that', "
        "'remember this', 'note this', or 'write this down'."
    )
    parameters = {
        "type": "OBJECT",
        "properties": {
            "content": {
                "type": "STRING",
                "description": (
                    "The exact note content to save (e.g., 'I need to prepare for my AI interview', "
                    "'Submit the assignment by Monday'). Exclude command trigger words."
                ),
            }
        },
        "required": ["content"],
    }

    async def execute(self, params: Dict[str, Any], session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        if not session:
            return {"error": "Database session unavailable."}

        raw_content = params.get("content", "")
        content = normalize_note_content(raw_content)
        if not content:
            return {"error": "Note content cannot be empty."}

        repo = NoteRepository(session)
        note = await repo.create_note(content=content)
        logger.info(f"Created note ID {note.id}: '{note.content}'")

        return {
            "id": note.id,
            "content": note.content,
            "created_at": note.created_at.strftime("%B %d, %Y at %I:%M %p"),
            "message": "Got it. I've saved that note.",
        }


class ListNotesTool(BaseTool):
    name = "list_notes"
    description = "Retrieve and list saved text notes."
    parameters = {"type": "OBJECT", "properties": {}}

    async def execute(self, params: Dict[str, Any], session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        if not session:
            return {"error": "Database session unavailable."}

        repo = NoteRepository(session)
        notes = await repo.list_notes()

        formatted_notes = []
        for n in notes:
            formatted_notes.append(
                {"id": n.id, "content": n.content, "created_at": n.created_at.strftime("%B %d, %Y at %I:%M %p")}
            )

        logger.info(f"Retrieved {len(formatted_notes)} notes.")
        return {"count": len(formatted_notes), "notes": formatted_notes}


tool_registry.register(CreateNoteTool())
tool_registry.register(ListNotesTool())
