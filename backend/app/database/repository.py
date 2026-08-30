from datetime import datetime
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Conversation, Message, Note, Reminder


class NoteRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_note(self, content: str) -> Note:
        note = Note(content=content)
        self.session.add(note)
        await self.session.commit()
        await self.session.refresh(note)
        return note

    async def list_notes(self) -> List[Note]:
        stmt = select(Note).order_by(Note.created_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_note(self, note_id: int) -> bool:
        stmt = select(Note).where(Note.id == note_id)
        result = await self.session.execute(stmt)
        note = result.scalar_one_or_none()
        if note:
            await self.session.delete(note)
            await self.session.commit()
            return True
        return False


class ReminderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_reminder(self, title: str, scheduled_datetime: datetime) -> Reminder:
        reminder = Reminder(title=title, scheduled_datetime=scheduled_datetime, status="pending")
        self.session.add(reminder)
        await self.session.commit()
        await self.session.refresh(reminder)
        return reminder

    async def list_reminders(self, status_filter: Optional[str] = None) -> List[Reminder]:
        stmt = select(Reminder)
        if status_filter:
            stmt = stmt.where(Reminder.status == status_filter)
        stmt = stmt.order_by(Reminder.scheduled_datetime.asc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def complete_reminder(self, reminder_id: int) -> Optional[Reminder]:
        stmt = select(Reminder).where(Reminder.id == reminder_id)
        result = await self.session.execute(stmt)
        reminder = result.scalar_one_or_none()
        if reminder:
            reminder.status = "completed"
            await self.session.commit()
            await self.session.refresh(reminder)
            return reminder
        return None

    async def delete_reminder(self, reminder_id: int) -> bool:
        stmt = select(Reminder).where(Reminder.id == reminder_id)
        result = await self.session.execute(stmt)
        reminder = result.scalar_one_or_none()
        if reminder:
            await self.session.delete(reminder)
            await self.session.commit()
            return True
        return False


class ConversationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create_conversation(self, conversation_id: str) -> Conversation:
        stmt = select(Conversation).where(Conversation.id == conversation_id)
        result = await self.session.execute(stmt)
        conversation = result.scalar_one_or_none()
        if not conversation:
            conversation = Conversation(id=conversation_id)
            self.session.add(conversation)
            await self.session.commit()
            await self.session.refresh(conversation)
        return conversation

    async def add_message(
        self, conversation_id: str, role: str, content: str, tool_name: Optional[str] = None
    ) -> Message:
        await self.get_or_create_conversation(conversation_id)
        msg = Message(conversation_id=conversation_id, role=role, content=content, tool_name=tool_name)
        self.session.add(msg)
        await self.session.commit()
        await self.session.refresh(msg)
        return msg

    async def get_recent_messages(self, conversation_id: str, limit: int = 20) -> List[Message]:
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def clear_conversation(self, conversation_id: str) -> bool:
        stmt = delete(Message).where(Message.conversation_id == conversation_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return True
