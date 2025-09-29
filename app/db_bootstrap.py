import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_postgres_fts(engine):
    """
    Thiết lập tìm kiếm toàn văn (full-text search) cho bảng kb_faq trong PostgreSQL.
    Thêm cột tsvector và chỉ mục GIN vào bảng kb_faq.
    """
    SessionLocal = sessionmaker(bind=engine)
    with SessionLocal() as session:
        try:
            # Thêm cột tsvector vào bảng kb_faq nếu chưa tồn tại
            session.execute(text("""
                ALTER TABLE kb_faq
                ADD COLUMN IF NOT EXISTS search_vector tsvector
                GENERATED ALWAYS AS (
                    to_tsvector('english', coalesce(question, '') || ' ' || coalesce(answer, ''))
                ) STORED;
            """))

            # Tạo chỉ mục GIN trên cột tsvector
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS kb_faq_search_vector_idx
                ON kb_faq USING GIN (search_vector);
            """))

            session.commit()
            logger.info("Thiết lập tìm kiếm toàn văn PostgreSQL hoàn tất cho bảng kb_faq")
        except Exception as e:
            logger.error(f"Lỗi khi thiết lập tìm kiếm toàn văn: {str(e)}", exc_info=True)
            session.rollback()
            raise