from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, constr, validator
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
    ConversationId: int = Field(..., description="Message belongs to ConversationID")
    Role: MessageRole = Field(..., description="Message Role")
    Content: constr(min_length=1, max_length=5000) = Field(..., description="Message Content")
    Sources: Optional[List[Source]] = Field(None, description="Message sources")

class MessageCreate(MessageBase):
    pass

class MessageUpdate(BaseModel):
    Role: Optional[MessageRole] = None
    Content: Optional[constr(min_length=1, max_length=5000)] = None
    Sources: Optional[List[Source]] = None


class MessageInDBBase(MessageBase):
    MessageId: int
    CreatedAt: datetime
    UpdatedAt: Optional[datetime] = None

    class Config:
        from_attributes = True

class Message(MessageInDBBase):
    pass

class MessageInDB(MessageInDBBase):
    pass