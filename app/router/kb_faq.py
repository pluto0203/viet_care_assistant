# app/routers/kb_faq.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models import KBCollection, Language
from app.schemas.kb_faq import KBFAQOut
from app.schemas.kb_collection import KBCollectionCreate, KBCollectionOut
from app.services.upload_faq import process_faq_file, insert_faqs_and_embeddings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kb_faq", tags=["kb_faq"])

@router.post("/{collection_id}/faqs/upload", response_model=list[KBFAQOut])
async def upload_faqs(
    collection_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Tải file JSON chứa FAQ và chèn vào kb_faq cho collection_id được chỉ định.
    """
    try:
        # Kiểm tra collection_id
        db_collection = db.query(KBCollection).filter(KBCollection.collection_id == collection_id).first()
        if not db_collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        # Xử lý file JSON và chèn FAQ
        cleaned_faqs = await process_faq_file(file)
        faq_records = insert_faqs_and_embeddings(db, collection_id, cleaned_faqs)
        return faq_records
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading FAQs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e

@router.post("/faqs/upload", response_model=list[KBFAQOut])
async def upload_faqs_with_collection(
    collection: KBCollectionCreate,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Tải file JSON chứa FAQ và tự động tạo collection nếu chưa tồn tại.
    """
    try:
        # Kiểm tra hoặc tạo collection
        db_collection = db.query(KBCollection).filter(KBCollection.name == collection.name).first()
        if not db_collection:
            db_collection = KBCollection(
                name=collection.name,
                description=collection.description,
                language=collection.language
            )
            db.add(db_collection)
            db.commit()
            db.refresh(db_collection)
            logger.info(f"Created collection: {collection.name} (ID: {db_collection.collection_id})")
        collection_id = db_collection.collection_id

        # Xử lý file JSON và chèn FAQ
        cleaned_faqs = await process_faq_file(file)
        faq_records = insert_faqs_and_embeddings(db, collection_id, cleaned_faqs)
        return faq_records
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error uploading FAQs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e