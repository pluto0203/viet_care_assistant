from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from enum import Enum

from app.database import Base

class Language(str, Enum):
    EN = "en"
    VI = "vi"
    ZH = "zh"

class KBCollection(Base):
    __tablename__ = "kb_collections"
    id = Column("collection_id", Integer, primary_key=True, index=True, autoincrement=True)
    name = Column("collection_name", String(50), unique=True, index=True, nullable=False)
    description = Column("description", Text)
    language = Column("language", String(16), default=Language.EN)
    created_at = Column("created_at", DateTime, default=datetime.now())
    updated_at = Column("updated_at", DateTime, default=datetime.now(), onupdate=datetime.now())
    faqs = relationship("KBFAQ", back_populates="collection")

class KBFAQ(Base):
    __tablename__ = "kb_faq"
    id = Column("faq_id", BigInteger, primary_key=True, index=True, autoincrement=True)
    collection_id = Column("collection_id", Integer, ForeignKey("kb_collections.collection_id", ondelete="CASCADE"), nullable=False)
    ext_id = Column("ext_id", Text)
    question = Column("question", Text, index=True)
    answer = Column("answer", Text)
    topic = Column("topic", Text, index=True)
    tags_json = Column("tags_json", JSONB, nullable=True)
    source = Column("source", JSONB, nullable=True)
    updated_at = Column("updated_at", DateTime, default=datetime.now(), onupdate=datetime.now())
    created_at = Column("created_at", DateTime, default=datetime.now())
    collection = relationship("KBCollection", back_populates="faqs")
    embeddings = relationship("KBFAQEmbedding", back_populates="faq", cascade="all, delete-orphan")

class KBFAQEmbedding(Base):
    __tablename__ = "kb_faq_embeddings"
    id = Column("faq_embedding_id", BigInteger, primary_key=True, index=True, autoincrement=True)
    faq_id = Column("faq_id", BigInteger, ForeignKey("kb_faq.faq_id", ondelete="CASCADE"), index=True, nullable=False)
    model = Column("model", String(100), nullable=False)
    dim = Column("dim", String(50), nullable=False)
    vector_json = Column("vector_json", JSONB, nullable=False)
    created_at = Column("created_at", DateTime, default=datetime.now())
    faq = relationship("KBFAQ", back_populates="embeddings")