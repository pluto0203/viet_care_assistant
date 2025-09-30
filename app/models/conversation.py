# app/models/conversation.py
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    conversation_id = Column("ConversationID", Integer, primary_key=True, index=True, autoincrement=True)
    userid = Column("UserID", Integer, ForeignKey("users.UserID"), index=True, nullable=True)
    topic = Column("Topic", String(200), nullable=True)
    created_at = Column("Create_at",DateTime, default=datetime.now(), index=True)

    #xuoi: conversation -> user
    user = relationship("User", back_populates="conversation")
    #nguoc: 1 conversation -> N messages
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
