import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_faqs_from_json(file_path):
    """
    Đọc dữ liệu FAQ từ file JSON và làm sạch.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            faqs = json.load(f)

        # Làm sạch dữ liệu
        cleaned_faqs = [
            {
                "ext_id": str(faq["Question_ID"]),  # Chuyển id thành chuỗi
                "question": clean_text(faq["Questions"]),
                "answer": clean_text(faq["Answers"]),
                "topic": None,
                "tags_json": None,
                "source": None
            }
            for faq in faqs
        ]
        logger.info(f"Đã đọc {len(cleaned_faqs)} FAQ từ file {file_path}")
        return cleaned_faqs
    except Exception as e:
        logger.error(f"Lỗi khi đọc file JSON: {str(e)}", exc_info=True)
        raise


def clean_text(text):
    """Xử lý các ký tự đặc biệt."""
    return text.replace("â€™", "'").replace("â", "")

