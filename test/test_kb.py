from fastapi.testclient import TestClient
from app.main import app
import json

client = TestClient(app)


def test_upload_faqs_new_collection():
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

        # Gửi request
        with open("test_faqs.json", "rb") as f:
            response = client.post(
                "/kb_faq/faqs/upload",
                files={"file": f},
                data={"name": "Test FAQs", "description": "Test collection", "language": "en"}
            )
        assert response.status_code == 200, "Không chèn được FAQ"
        assert len(response.json()) == 1, "Số FAQ chèn không đúng"
        assert response.json()[0]["question"] == "What is mental illness?", "Câu hỏi không khớp"

        logger.info("Kiểm thử upload FAQ với collection mới thành công")
    except Exception as e:
        logger.error(f"Kiểm thử thất bại: {str(e)}", exc_info=True)
        raise