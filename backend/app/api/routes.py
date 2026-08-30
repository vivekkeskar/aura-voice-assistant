from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.database import get_db
from app.database.repository import NoteRepository, ReminderRepository

router = APIRouter(prefix="/api", tags=["API"])


class NoteCreateSchema(BaseModel):
    content: str


class ReminderCreateSchema(BaseModel):
    title: str
    scheduled_datetime: str


# Notes Endpoints
@router.get("/notes")
async def list_notes(db: AsyncSession = Depends(get_db)):
    repo = NoteRepository(db)
    notes = await repo.list_notes()
    return [n.to_dict() for n in notes]


@router.post("/notes")
async def create_note(data: NoteCreateSchema, db: AsyncSession = Depends(get_db)):
    if not data.content.strip():
        raise HTTPException(status_code=400, detail="Note content cannot be empty")
    repo = NoteRepository(db)
    note = await repo.create_note(data.content.strip())
    return note.to_dict()


@router.delete("/notes/{note_id}")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)):
    repo = NoteRepository(db)
    success = await repo.delete_note(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"status": "success", "message": f"Note {note_id} deleted"}


# Reminders Endpoints
@router.get("/reminders")
async def list_reminders(status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    repo = ReminderRepository(db)
    reminders = await repo.list_reminders(status_filter=status)
    return [r.to_dict() for r in reminders]


@router.post("/reminders/{reminder_id}/complete")
async def complete_reminder(reminder_id: int, db: AsyncSession = Depends(get_db)):
    repo = ReminderRepository(db)
    reminder = await repo.complete_reminder(reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return reminder.to_dict()


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(reminder_id: int, db: AsyncSession = Depends(get_db)):
    repo = ReminderRepository(db)
    success = await repo.delete_reminder(reminder_id)
    if not success:
        raise HTTPException(status_code=404, detail="Reminder not found")
    return {"status": "success", "message": f"Reminder {reminder_id} deleted"}
