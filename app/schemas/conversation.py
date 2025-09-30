#app/schemas/conversation.py

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.schemas.message import Message


class ConversationBase(BaseModel):
    userid: Optional[int] = None
    topic : Optional[str] = None

class ConversationCreate(ConversationBase):
    pass

class ConversationUpdate(BaseModel):
    topic: Optional[str] = None

class ConversationInDBBase(ConversationBase):
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class Conversation(ConversationInDBBase):
    messages: List[Message] = []

class ConversationInDB(ConversationInDBBase):
    pass