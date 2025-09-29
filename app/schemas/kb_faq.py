from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any

class KBFAQCreate(BaseModel):
    ext_id: str
    question: str
    answer: str
    topic: Optional[str] = None
    tags_json: Optional[Dict[str, Any]] = None
    source: Optional[Dict[str, Any]] = None

class KBFAQOut(BaseModel):
    faq_id: int
    collection_id: int
    ext_id: str
    question: str
    answer: str
    topic: Optional[str]
    tags_json: Optional[Dict[str, Any]]
    source: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True