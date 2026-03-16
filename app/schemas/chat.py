from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageBase(BaseModel):
    role: str
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: int
    session_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class SessionBase(BaseModel):
    project_id: int


class SessionCreate(SessionBase):
    pass


class Session(SessionBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
