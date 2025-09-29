#app/router/kb_collection.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models.knowledge_base import KBCollection, Language
from app.schemas.kb_collection import KBCollectionCreate, KBCollectionOut

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb_collections", tags=["kb_collections"])

@router.post("/collections/", response_model=KBCollectionOut)
def create_collection(collection: KBCollectionCreate, db: Session = Depends(get_db)):
    """
    Tạo một collection mới trong bảng kb_collections.
    """
    try:
        db_collection = db.query(KBCollection).filter(KBCollection.name == collection.name).first()
        if db_collection:
            raise HTTPException(status_code=400, detail="Collection name already exists")

        new_collection = KBCollection(
            name=collection.name,
            description=collection.description,
            language=collection.language
        )
        db.add(new_collection)
        db.commit()
        db.refresh(new_collection)
        logger.info(f"Created collection: {collection.name} (ID: {new_collection.collection_id})")
        return new_collection
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating collection: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e