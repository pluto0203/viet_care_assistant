import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import Config
from app.models import KBFAQ, KBFAQEmbedding, Language
from sentence_transformers import SentenceTransformer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def insert_faqs_with_embeddings(engine, faqs, collection_id, model_name="all-MiniLM-L6-v2"):
    model = SentenceTransformer(model_name)
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        try:
            for faq in faqs:
                faq_record = KBFAQ(
                    collection_id=collection_id,
                    ext_id=faq["ext_id"],
                    question=faq["question"],
                    answer=faq["answer"],
                    topic=faq.get("topic"),
                    tags_json=faq.get("tags_json"),
                    source=faq.get("source")
                )
                session.add(faq_record)
                session.flush()  # Lấy faq_id

                text = faq["question"] + " " + faq["answer"]
                embedding = model.encode([text])[0]
                embedding_record = KBFAQEmbedding(
                    faq_id=faq_record.faq_id,
                    model=model_name,
                    dim=str(embedding.shape[0]),
                    vector_json=embedding.tolist()  # Hoặc vector=embedding nếu dùng pgvector
                )
                session.add(embedding_record)
            session.commit()
            logger.info(f"Đã chèn {len(faqs)} FAQ và embeddings vào collection {collection_id}")
        except Exception as e:
            logger.error(f"Lỗi: {str(e)}", exc_info=True)
            session.rollback()
            raise


# Quy trình chính
def main():
    # Kết nối cơ sở dữ liệu
    config = Config()
    engine = create_engine(config.DATABASE_URL)

    # Tạo schema và FTS
    bootstrap_database(engine)

    # Đọc file JSON
    file_path = "path/to/your/faqs.json"
    faqs = load_faqs_from_json(file_path)

    # Tạo collection
    collection_id = create_collection(
        engine,
        name="Mental Health FAQs",
        description="FAQs about mental health issues",
        language=Language.EN
    )

    # Chèn FAQ và embeddings
    insert_faqs_with_embeddings(engine, faqs, collection_id)


if __name__ == "__main__":
    main()