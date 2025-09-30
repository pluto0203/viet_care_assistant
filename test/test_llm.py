# tests/test_chat.py
from fastapi.testclient import TestClient
from app.app_main import app
import json
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


client = TestClient(app)

def test_chat_conversation():
    try:
        # Tạo file JSON tạm
        test_faqs = [
            {
                "Question_ID": "test_1",
                "Questions": "What is mental illness?",
                "Answers": "A health condition affecting thoughts and emotions."
            }
        ]
        with open("test_faqs.json", "w") as f:
            json.dump(test_faqs, f)

        # Upload FAQ
        with open("test_faqs.json", "rb") as f:
            response = client.post(
                "/kb_faq/faqs/upload",
                files={"file": f},
                data={"name": "Test FAQs", "description": "Test collection", "language": "en"}
            )
        assert response.status_code == 200, "Không chèn được FAQ"
        collection_id = response.json()[0]["collection_id"]

        # Tạo conversation
        response = client.post(
            f"/chat/{collection_id}/conversations",
            json={"UserID": 1, "Topic": "Mental Health"}
        )
        assert response.status_code == 200, "Không tạo được conversation"
        conversation_id = response.json()["ConversationID"]

        # Gửi tin nhắn
        response = client.post(
            f"/chat/{collection_id}/conversations/{conversation_id}/messages",
            json={
                "ConversationId": conversation_id,
                "Role": "user",
                "Content": "What is mental illness?"
            }
        )
        assert response.status_code == 200, "Không gửi được tin nhắn"
        assert response.json()["Role"] == "assistant", "Phản hồi không phải từ assistant"
        assert "mental" in response.json()["Content"].lower(), "Phản hồi không đúng"

        logger.info("Kiểm thử chat với OpenRouter thành công")
    except Exception as e:
        logger.error(f"Kiểm thử thất bại: {str(e)}", exc_info=True)
        raise
    finally:
        if os.path.exists("test_faqs.json"):
            os.remove("test_faqs.json")