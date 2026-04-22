# Viet Care Assistant 🤖

Trợ lý y tế – Streamlit + FastAPI + RAG

<p align="center">
  <a href="#tính-năng-chính">Tính năng</a> •
  <a href="#kiến-trúc--luồng-xử-lý">Kiến trúc</a> •
  <a href="#cách-chạy">Cách chạy</a> •
  <a href="#cấu-hình">Cấu hình</a> •
  <a href="#api-quick-reference">API Quick Reference</a> •
  <a href="#thư-mục--công-nghệ">Thư mục & Công nghệ</a> •
  <a href="#xử-lý-lỗi">Xử lý lỗi</a> •
  <a href="#lộ-trình">Lộ trình</a> •
  <a href="#giấy-phép">Giấy phép</a>
</p>

## Tính năng chính

- **Hỏi đáp y tế**: Giao diện trò chuyện đơn giản.
- **Giao diện thân thiện**: Header rõ ràng, bong bóng chat (user/assistant).
- **Quản lý hội thoại**: Lưu lịch sử chat trong session, hỗ trợ làm mới lịch sử.
- **Bảo mật cơ bản**: Đăng ký/đăng nhập với JWT.
- **Quản lý kiến thức**: Tạo collection (`/kb_collections`) và upload FAQ file JSON (`/kb_faq`).
- **RAG**: Hỗ trợ RAG cho phản hồi dựa trên knowledge base.

**Lưu ý**: Đây là phiên bản MVP. Nếu gặp lỗi 422 trong chat, xem phần [Xử lý lỗi](#xử-lý-lỗi).

## Kiến trúc & luồng xử lý




## Cách chạy

### 1) Backend (FastAPI)

```bash
# Tạo virtual environment (khuyến nghị)
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# hoặc .venv\Scripts\activate  # Windows

# Cài dependencies
pip install -r requirements.txt  # Bao gồm fastapi, uvicorn, sqlalchemy, ...

# Chạy server
uvicorn app.app_main:app --host 127.0.0.1 --port 18080

