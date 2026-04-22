# app/router/kb_faq.py
"""
Knowledge Base FAQ Router — upload and manage FAQ data.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models import KBCollection
from app.schemas.kb_faq import KBFAQOut
from app.schemas.kb_collection import KBCollectionCreate
from app.services.upload_faq import process_faq_file, insert_faqs_and_embeddings
from app.services.llm import get_llm_service
from app.core.exceptions import CollectionNotFound, InvalidFileFormat
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/kb_faq", tags=["kb_faq"])


@router.post("/{collection_id}/faqs/upload", response_model=list[KBFAQOut])
async def upload_faqs(
    collection_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload a JSON file containing FAQs into an existing collection."""
    try:
        # Validate collection exists
        db_collection = (
            db.query(KBCollection)
            .filter(KBCollection.collection_id == collection_id)
            .first()
        )
        if not db_collection:
            raise CollectionNotFound(collection_id)

        # Process and insert FAQs
        cleaned_faqs = await process_faq_file(file)
        faq_records = insert_faqs_and_embeddings(db, collection_id, cleaned_faqs)

        # Invalidate vector store cache so new FAQs are picked up
        llm_service = get_llm_service()
        llm_service.invalidate_cache(collection_id)

        logger.info("faqs_uploaded", collection_id=collection_id, count=len(faq_records))
        return faq_records

    except CollectionNotFound as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error("faq_upload_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/faqs/upload", response_model=list[KBFAQOut])
async def upload_faqs_with_collection(
    collection: KBCollectionCreate,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Upload FAQs and auto-create collection if it doesn't exist."""
    try:
        # Find or create collection
        db_collection = (
            db.query(KBCollection)
            .filter(KBCollection.name == collection.name)
            .first()
        )
        if not db_collection:
            db_collection = KBCollection(
                name=collection.name,
                description=collection.description,
                language=collection.language,
            )
            db.add(db_collection)
            db.commit()
            db.refresh(db_collection)
            logger.info(
                "collection_auto_created",
                name=collection.name,
                collection_id=db_collection.collection_id,
            )

        # Process and insert FAQs
        cleaned_faqs = await process_faq_file(file)
        faq_records = insert_faqs_and_embeddings(
            db, db_collection.collection_id, cleaned_faqs
        )

        logger.info(
            "faqs_uploaded_with_collection",
            collection_id=db_collection.collection_id,
            count=len(faq_records),
        )
        return faq_records

    except SQLAlchemyError as e:
        db.rollback()
        logger.error("faq_upload_db_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")