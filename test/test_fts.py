import pytest
import logging
from sqlalchemy import create_engine, text, NullPool
from sqlalchemy.orm import sessionmaker
from app.config import Config
from app.db_bootstrap import ensure_postgres_fts

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
config = Config()
# DATABASE_URL phải sử dụng psycopg2, ví dụ: "postgresql+psycopg2://user:password@localhost:5432/dbname"
engine = create_engine(config.DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

def test_fts_setup():
    try:
        # Thiết lập FTS
        ensure_postgres_fts(engine)

        with SessionLocal() as session:
            # Kiểm tra bảng kb_faq tồn tại
            result = session.execute(text("SELECT 1 FROM pg_tables WHERE tablename = 'kb_faq'"))
            assert result.scalar() is not None, "Bảng kb_faq không tìm thấy"

            # Kiểm tra cột search_vector tồn tại
            result = session.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'kb_faq' AND column_name = 'search_vector'
            """))
            assert result.scalar() is not None, "Cột search_vector không tìm thấy"

            # Kiểm tra chỉ mục GIN tồn tại
            result = session.execute(text("""
                SELECT indexname FROM pg_indexes
                WHERE tablename = 'kb_faq' AND indexname = 'kb_faq_search_vector_idx'
            """))
            assert result.scalar() is not None, "Chỉ mục GIN không tìm thấy"

            logger.info("Kiểm thử thiết lập FTS thành công")
    except Exception as e:
        logger.error(f"Kiểm thử thiết lập FTS thất bại: {str(e)}", exc_info=True)
        raise