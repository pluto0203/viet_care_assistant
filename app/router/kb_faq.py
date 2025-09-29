import json
import logging
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models import KBCollection, KBFAQ, KBFAQEmbedding, Language
from app.schemas.kb_faq import KBFAQOut, KBFAQCreate
from app.schemas.kb_collection import KBCollectionCreate, KBCollectionOut
from sentence_transformers import SentenceTransformer

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

        # Đọc file JSON
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be JSON")
        content = await file.read()
        faqs = json.loads(content.decode('utf-8'))

        # Làm sạch và chuẩn bị dữ liệu
        model = SentenceTransformer('all-MiniLM-L6-v2')
        cleaned_faqs = [
            {
                "ext_id": str(faq["Question_ID"]),
                "question": clean_text(faq["Questions"]),
                "answer": clean_text(faq["Answers"]),
                "topic": None,
                "tags_json": None,
                "source": None
            }
            for faq in faqs
        ]

        # Chèn FAQ và embeddings
        faq_records = []
        for faq in cleaned_faqs:
            faq_record = KBFAQ(
                collection_id=collection_id,
                ext_id=faq["ext_id"],
                question=faq["question"],
                answer=faq["answer"],
                topic=faq["topic"],
                tags_json=faq["tags_json"],
                source=faq["source"]
            )
            db.add(faq_record)
            db.flush()  # Lấy faq_id

            # Tạo embedding
            text = faq["question"] + " " + faq["answer"]
            embedding = model.encode([text])[0]
            embedding_record = KBFAQEmbedding(
                faq_id=faq_record.faq_id,
                model="all-MiniLM-L6-v2",
                dim=str(embedding.shape[0]),
                vector_json=embedding.tolist()
            )
            db.add(embedding_record)
            faq_records.append(faq_record)

        db.commit()
        logger.info(f"Đã chèn {len(faq_records)} FAQ vào collection {collection_id}")
        return faq_records
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error uploading FAQs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e

def clean_text(text):
    return text.replace("â€™", "'").replace("â", "")