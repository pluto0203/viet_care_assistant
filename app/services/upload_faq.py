# app/services/upload_faq.py
import json
import logging
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status, UploadFile
from app.models import KBCollection, KBFAQ, KBFAQEmbedding
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Làm sạch văn bản, loại bỏ ký tự đặc biệt.
    """
    return text.replace("â€™", "'").replace("â", "")


async def process_faq_file(file: UploadFile) -> list[dict]:
    """
    Đọc và làm sạch dữ liệu từ file JSON.
    """
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="File must be JSON")
    content = await file.read()
    faqs = json.loads(content.decode('utf-8'))

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
    logger.info(f"Đã đọc và làm sạch {len(cleaned_faqs)} FAQ từ file")
    return cleaned_faqs


def insert_faqs_and_embeddings(db: Session, collection_id: int, faqs: list[dict]) -> list[KBFAQ]:
    """
    Chèn FAQ và embeddings vào cơ sở dữ liệu.
    """
    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
        faq_records = []

        for faq in faqs:
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

            text = faq["question"] + " " + faq["answer"]
            embedding = model.encode([text])[0]
            embedding_record = KBFAQEmbedding(
                faq_id=faq_record.faq_id,
                model="all-MiniLM-L6-v2",
                dim= int(embedding.shape[0]),
                vector_json=embedding.tolist()
            )
            db.add(embedding_record)
            faq_records.append(faq_record)

        db.commit()
        logger.info(f"Đã chèn {len(faq_records)} FAQ vào collection {collection_id}")
        return faq_records
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error inserting FAQs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e