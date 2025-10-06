from typing import Optional, List
from pydantic import BaseModel, Field, constr
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Source(BaseModel):
    url: str
    title: Optional[str] = None
    description: Optional[str] = None

class MessageBase(BaseModel):
    conversation_id: int = Field(..., description="Message belongs to ConversationID")
    role: MessageRole = Field(..., description="Message Role")
    content: constr(min_length=1, max_length=5000) = Field(..., description="Message Content")

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    role: Optional[MessageRole] = None
    content: Optional[constr(min_length=1, max_length=5000)] = None
    Sources: Optional[List[Source]] = None

class MessageInDBBase(MessageBase):
    message_id: int
    created_at: datetime  # Sửa từ CreatedAt

    class Config:
        from_attributes = True

class Message(MessageInDBBase):
    pass

class MessageInDB(MessageInDBBase):
    pass