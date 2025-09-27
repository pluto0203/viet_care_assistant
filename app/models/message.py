# app/models/message.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy.dialects.postgresql import JSONB

class Message(Base):
    __tablename__ = "messages"
    MessageID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ConversationID = Column(Integer, ForeignKey("conversations.ConversationID", ondelete="CASCADE"), index=True, nullable=False)

    Role = Column(String(20), nullable=False)            # "user" | "assistant" | "system"
    Content = Column(String, nullable=False)             # dùng TEXT bằng String (SQLAlchemy map sang TEXT/VARCHAR tùy DB)
    Sources = Column(JSONB, nullable=True)               # ví dụ: [{"doc_id":123,"chunk_id":45,"score":0.82}, ...]
    Created_at = Column(DateTime, default=datetime.now(), index=True)

    conversation = relationship("Conversation", back_populates="messages")
