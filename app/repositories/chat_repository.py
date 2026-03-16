from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.repositories.user_repository import BaseRepository
from app.models.chat import Session, Message
from app.schemas.chat import SessionCreate, MessageCreate


class ChatRepository(BaseRepository[Session, SessionCreate, None]):
    def __init__(self, db: AsyncSession):
        super().__init__(Session, db)

    async def create_session(self, session_in: SessionCreate) -> Session:
        return await self.create(session_in)

    async def add_message(self, session_id: int, message_in: MessageCreate) -> Message:
        db_obj = Message(session_id=session_id, **message_in.model_dump())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def get_history(self, session_id: int) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .filter(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_session_by_id(self, session_id: int) -> Optional[Session]:
        return await self.get_by_id(session_id)
