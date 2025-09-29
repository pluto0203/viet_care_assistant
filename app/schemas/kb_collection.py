#app/schemas/kn_collection
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class Language(str, Enum):
    EN = "en"
    VI = "vi"
    ZH = "zh"

class KBCollectionCreate(BaseModel):
    name: str
    description: str | None = None
    language: Language = Language.EN

class KBCollectionOut(BaseModel):
    collection_id: int
    name: str
    description: str | None = None
    language: Language
    created_at: datetime

    class Config:
        from_attributes = True
    