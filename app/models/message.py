# app/models/message.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from sqlalchemy.dialects.postgresql import JSONB

class Message(Base):
    __tablename__ = "messages"
    message_id = Column("MessageID",Integer, primary_key=True, index=True, autoincrement=True)
    conversation_id = Column("ConversationID", Integer, ForeignKey("conversations.ConversationID", ondelete="CASCADE"), index=True, nullable=False)

    role = Column("Role", String(20), nullable=False)            # "user" | "assistant" | "system"
    content = Column("Content", String, nullable=False)             # dùng TEXT bằng String (SQLAlchemy map sang TEXT/VARCHAR tùy DB)
    sources = Column("Sources", JSONB, nullable=True)               # ví dụ: [{"doc_id":123,"chunk_id":45,"score":0.82}, ...]
    created_at = Column("Create_at",DateTime, default=datetime.now(), index=True)

    #xuoi: message -> conversation
    conversation = relationship("Conversation", back_populates="messages")
