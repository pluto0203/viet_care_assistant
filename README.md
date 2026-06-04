# VietCare Assistant

Hệ thống hỏi đáp y tế thông minh xây dựng bằng FastAPI, được vận hành bởi **Tool-calling Agent** kết hợp RAG (Retrieval-Augmented Generation).

> Người dùng hỏi → Agent phân tích → chọn đúng công cụ → tổng hợp câu trả lời có nguồn trích dẫn.

---

## Mục lục

- [Tổng quan](#tổng-quan)
- [Đây là Agent, không phải LLM thông thường](#đây-là-agent-không-phải-llm-thông-thường)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Công nghệ sử dụng](#công-nghệ-sử-dụng)
- [Cài đặt và chạy](#cài-đặt-và-chạy)
- [API Endpoints](#api-endpoints)
- [Cấu trúc project](#cấu-trúc-project)
- [Kiểm thử](#kiểm-thử)
- [Biến môi trường](#biến-môi-trường)
- [Câu hỏi thường gặp](#câu-hỏi-thường-gặp)

---

## Tổng quan

VietCare Assistant là hệ thống hỏi đáp y tế thông minh, hỗ trợ người dùng tìm kiếm thông tin sức khỏe và cơ sở y tế gần nhất. Hệ thống không chỉ tra cứu kiến thức tĩnh mà còn có khả năng **lập luận, lựa chọn công cụ phù hợp và phối hợp nhiều nguồn thông tin** để đưa ra câu trả lời chính xác.

**Tính năng chính:**

- **Agent Q&A y tế** — tự động lựa chọn giữa tra cứu KB nội bộ và tìm bệnh viện gần nhất
- **Hội thoại nhiều lượt** — ghi nhớ ngữ cảnh, hỗ trợ câu hỏi nối tiếp
- **Phản hồi streaming** — Server-Sent Events (SSE) cho trải nghiệm chat realtime
- **Quản lý Knowledge Base** — upload bộ FAQ, tự động xây dựng vector store
- **Xác thực bảo mật** — JWT + Argon2 password hashing
- **Sẵn sàng Docker** — triển khai một lệnh với `docker compose up`

---

## Đây là Agent, không phải LLM thông thường

Đây là điểm cốt lõi phân biệt VietCare với một chatbot RAG thông thường.

### LLM + RAG thông thường hoạt động như thế nào?

```
Người dùng hỏi
      │
      ▼
[LUÔN LUÔN] Tìm kiếm KB bằng FAISS
      │
      ▼
Ghép context vào prompt
      │
      ▼
Gọi LLM → Trả lời
```

Pipeline này **cố định**: mọi câu hỏi đều chạy qua bước tìm KB, dù câu hỏi đó cần hay không. LLM không có quyền quyết định bất kỳ điều gì — nó chỉ nhận input và sinh output.

### Agent (VietCare) hoạt động như thế nào?

```
Người dùng hỏi
      │
      ▼
Agent nhận câu hỏi → LLM phân tích
      │
      ├── Cần tìm thông tin y tế?   ──► Gọi search_knowledge_base()
      │                                         │
      ├── Cần tìm bệnh viện gần?    ──► Gọi find_nearby_hospitals()
      │                                         │
      ├── Cần cả hai?                ──► Gọi lần lượt cả hai tools
      │
      ▼
LLM nhận kết quả từ tools → Tổng hợp → Trả lời
```

LLM **tự quyết định** khi nào cần dùng tool nào, gọi bao nhiêu lần, theo thứ tự nào. Đây là hành vi **lập luận** — không phải pipeline cứng nhắc.

### So sánh trực tiếp

| Tiêu chí | LLM + RAG thông thường | VietCare Agent |
|---|---|---|
| **Luồng xử lý** | Cố định (hardcoded pipeline) | Động — LLM tự quyết định |
| **Sử dụng công cụ** | Luôn dùng RAG, không có lựa chọn | Chọn công cụ phù hợp theo câu hỏi |
| **Kết hợp nhiều công cụ** | Không | Có thể gọi nhiều tools theo thứ tự |
| **Tìm bệnh viện** | Không thể | Có (Nominatim + Overpass API) |
| **Câu hỏi không cần KB** | Vẫn tốn chi phí tìm kiếm | Trả lời thẳng, không gọi tool |
| **Mở rộng thêm công cụ** | Phải sửa pipeline | Thêm tool mới vào registry |

### Cơ chế kỹ thuật: OpenAI Function Calling

VietCare dùng **OpenAI Function Calling** (qua OpenRouter) — một giao thức cho phép LLM yêu cầu gọi hàm bên ngoài thay vì tự bịa thông tin.

**Luồng chi tiết:**

```
Bước 1: Hệ thống gửi câu hỏi + danh sách tool schemas cho LLM
         ↓
Bước 2: LLM phân tích và quyết định: "Câu hỏi này cần tool gì?"
         ↓
Bước 3a: Nếu cần tool → LLM trả về {"tool": "search_knowledge_base", "args": {...}}
         ↓
Bước 3b: Hệ thống thực thi tool, lấy kết quả thực tế
         ↓
Bước 4: Kết quả được đưa vào messages, LLM đọc và tiếp tục xử lý
         ↓
Bước 5: Lặp lại tối đa 5 vòng (giới hạn MAX_ITERATIONS)
         ↓
Bước 6: LLM không còn cần tool nào → sinh câu trả lời cuối cùng
```

**Điểm mấu chốt:** Ở Bước 3a, LLM *yêu cầu* gọi hàm, không phải LLM *tự chạy* hàm. Code Python (VietCare) mới thực sự chạy hàm và trả kết quả lại cho LLM. LLM không có khả năng tự truy cập internet hay database — nó chỉ mô tả *muốn* làm gì, còn hệ thống quyết định *làm* hay không.

### Các công cụ (Tools) hiện tại

**Công cụ 1: `search_knowledge_base`**

Tìm kiếm trong knowledge base nội bộ bằng FAISS vector search. Được kích hoạt khi người dùng hỏi về triệu chứng, bệnh lý, sức khỏe tâm thần, thông tin y tế chung.

```
Câu hỏi → HuggingFace Embeddings → FAISS similarity search → Top-K tài liệu → context
```

**Công cụ 2: `find_nearby_hospitals`**

Tìm bệnh viện/phòng khám gần một địa điểm. Được kích hoạt khi người dùng hỏi tìm cơ sở y tế.

```
"quận 1 HCM" → Nominatim geocoding → tọa độ lat/lng
             → Overpass API (OpenStreetMap)
             → danh sách bệnh viện sắp xếp theo khoảng cách
```

Cả hai dịch vụ địa lý đều **miễn phí và không cần API key**.

---

## Kiến trúc hệ thống

```
┌─────────────────┐        ┌────────────────────────────────────────────────┐
│    Giao diện     │        │                  FastAPI Backend                │
│   (Streamlit)    │──────▶ │                                                │
└─────────────────┘        │  ┌──────────┐   ┌─────────────────────────┐   │
                            │  │  Router  │──▶│      ChatService        │   │
                            │  │  (HTTP)  │   │  (Quản lý hội thoại)   │   │
                            │  └──────────┘   └──────────┬──────────────┘   │
                            │                            │                   │
                            │                 ┌──────────▼──────────┐        │
                            │                 │    AgentService      │        │
                            │                 │  ┌───────────────┐  │        │
                            │                 │  │  Vòng lặp     │  │        │
                            │                 │  │  Agent        │  │        │
                            │                 │  │ (tối đa 5     │  │        │
                            │                 │  │  vòng lặp)    │  │        │
                            │                 │  └──────┬────────┘  │        │
                            │                 └─────────┼───────────┘        │
                            │                           │                    │
                            │              ┌────────────┴────────────┐       │
                            │              │                         │       │
                            │   ┌──────────▼──────────┐  ┌──────────▼─────┐ │
                            │   │  search_knowledge    │  │ find_nearby_   │ │
                            │   │     _base()          │  │ hospitals()    │ │
                            │   │                      │  │                │ │
                            │   │  FAISS + HuggingFace │  │  Nominatim API │ │
                            │   │  Embeddings          │  │  Overpass API  │ │
                            │   └──────────────────────┘  └────────────────┘ │
                            │                                                 │
                            │   ┌─────────────────────────────────────────┐  │
                            │   │          OpenRouter (LLM)               │  │
                            │   │   DeepSeek / GPT / Claude / ...         │  │
                            │   └─────────────────────────────────────────┘  │
                            │                                                 │
                            │   ┌─────────────────────────────────────────┐  │
                            │   │        PostgreSQL (Supabase)            │  │
                            │   │  Users / Conversations / Messages / KB  │  │
                            │   └─────────────────────────────────────────┘  │
                            └────────────────────────────────────────────────┘
```

### Phân tầng trách nhiệm

| Tầng | Trách nhiệm |
|---|---|
| **Router** | Nhận HTTP request, validate input, trả HTTP response — không chứa business logic |
| **ChatService** | Quản lý vòng đời hội thoại, lưu tin nhắn vào DB, gọi AgentService |
| **AgentService** | Vòng lặp agent: gọi LLM → thực thi tools → lặp → sinh câu trả lời |
| **LLMService** | Quản lý FAISS vector store, cung cấp `retrieve_context()` cho KB tool |
| **Tools** | Các hàm độc lập: `search_knowledge_base`, `find_nearby_hospitals` |

---

## Công nghệ sử dụng

| Tầng | Công nghệ |
|---|---|
| **API Framework** | FastAPI (async, OpenAPI docs tự động) |
| **Cơ sở dữ liệu** | PostgreSQL (Supabase) + SQLAlchemy 2.0 |
| **Xác thực** | JWT + Argon2 password hashing |
| **Tìm kiếm vector** | FAISS + HuggingFace Embeddings (`all-MiniLM-L6-v2`) |
| **Agent / LLM** | OpenAI Function Calling qua OpenRouter |
| **Mô hình LLM** | DeepSeek, GPT-4, Claude, ... (cấu hình qua `LLM_MODEL`) |
| **Tìm kiếm bệnh viện** | Nominatim (geocoding) + Overpass API (OpenStreetMap) |
| **HTTP Client** | httpx |
| **Cấu hình** | Pydantic Settings (kiểm tra khi khởi động) |
| **Logging** | structlog (JSON trong production, màu sắc trong dev) |
| **DevOps** | Docker, Docker Compose |
| **Giao diện** | Streamlit |

---

## Cài đặt và chạy

### Cách 1: Docker (Khuyến nghị)

```bash
git clone https://github.com/pluto0203/viet_care_assistant.git
cd viet_care_assistant
cp .env.example .env   # Điền các giá trị cần thiết
docker compose up --build
```

### Cách 2: Chạy local

```bash
# Tạo môi trường ảo
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate         # Windows

# Cài dependencies
pip install -e ".[dev]"

# Cấu hình biến môi trường
cp .env.example .env             # Điền API keys và thông tin DB

# Chạy backend
uvicorn app.app_main:app --host 127.0.0.1 --port 18080 --reload

# Chạy giao diện (terminal khác)
streamlit run app/frontend/app.py
```

**Lưu ý về Vector Store:** Vector store (FAISS index) không được lưu trong repo. Hệ thống sẽ tự động build từ database khi có câu hỏi đầu tiên. Nếu muốn chuẩn bị sẵn, upload bộ FAQ qua endpoint `/kb_faq/{id}/faqs/upload` sau khi khởi động.

---

## API Endpoints

| Endpoint | Phương thức | Mô tả |
|---|---|---|
| `GET /` | GET | Thông tin API |
| `GET /health` | GET | Kiểm tra trạng thái (DB, LLM) |
| `POST /auth/register` | POST | Tạo tài khoản mới |
| `POST /auth/login` | POST | Đăng nhập, nhận JWT token |
| `POST /chat/{id}/conversations` | POST | Tạo cuộc hội thoại mới |
| `POST /chat/{id}/conversations/{cid}/messages` | POST | Gửi tin nhắn (đồng bộ) |
| `POST /chat/{id}/conversations/{cid}/stream` | POST | Gửi tin nhắn (SSE streaming) |
| `POST /kb_faq/{id}/faqs/upload` | POST | Upload bộ FAQ |

Tài liệu API tương tác: `http://localhost:18080/docs`

---

## Cấu trúc project

```
viet_care_assistant/
├── app/
│   ├── app_main.py              # Điểm khởi đầu FastAPI, middleware, lifespan
│   ├── config.py                # Pydantic Settings, kiểm tra biến môi trường
│   ├── database.py              # SQLAlchemy engine & session
│   ├── core/
│   │   ├── exceptions.py        # Hệ thống exception tùy chỉnh
│   │   └── logging.py           # Cấu hình structlog
│   ├── models/                  # SQLAlchemy ORM models
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── knowledge_base.py
│   ├── schemas/                 # Pydantic request/response schemas
│   ├── router/                  # HTTP handlers (tầng mỏng)
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── health.py
│   │   ├── kb_collection.py
│   │   └── kb_faq.py
│   ├── services/                # Tầng business logic
│   │   ├── agent_service.py     # ★ Vòng lặp Agent (tool-calling)
│   │   ├── chat_service.py      # Quản lý hội thoại và tin nhắn
│   │   ├── llm.py               # FAISS vector store & embeddings
│   │   ├── auth.py              # JWT & mã hóa mật khẩu
│   │   ├── upload_faq.py        # Pipeline nhập FAQ
│   │   └── tools/               # ★ Các công cụ của Agent
│   │       ├── kb_tool.py       #   search_knowledge_base
│   │       └── hospital_tool.py #   find_nearby_hospitals
│   └── frontend/                # Giao diện Streamlit
├── tests/                       # Kiểm thử đơn vị và tích hợp
├── data/                        # Bộ dữ liệu FAQ (CSV, JSON)
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

---

## Kiểm thử

```bash
# Chạy toàn bộ test
pytest

# Kèm báo cáo coverage
pytest --cov=app --cov-report=html

# Kiểm thử từng module
pytest tests/test_agent_service.py -v
pytest tests/test_hospital_tool.py -v
pytest tests/test_kb_tool.py -v
pytest tests/test_auth.py -v
```

---

## Biến môi trường

| Biến | Bắt buộc | Mô tả | Mặc định |
|---|---|---|---|
| `user` | Có | Tên đăng nhập database | — |
| `password` | Có | Mật khẩu database | — |
| `host` | Có | Host database | — |
| `port` | Không | Cổng database | `5432` |
| `dbname` | Có | Tên database | — |
| `SECRET_KEY` | Có | Khóa ký JWT | — |
| `OPENROUTER_API_KEY` | Có | API key OpenRouter | — |
| `LLM_MODEL` | Không | ID mô hình LLM | `deepseek/deepseek-chat-v3.1:free` |
| `LLM_TEMPERATURE` | Không | Độ ngẫu nhiên của LLM | `0.7` |
| `LLM_MAX_TOKENS` | Không | Số token tối đa mỗi phản hồi | `2048` |
| `EMBEDDING_MODEL` | Không | Mô hình embedding HuggingFace | `all-MiniLM-L6-v2` |
| `RAG_TOP_K` | Không | Số tài liệu lấy từ FAISS | `5` |
| `MAX_HISTORY_MESSAGES` | Không | Số tin nhắn lịch sử đưa vào context | `10` |
| `DEBUG` | Không | Chế độ debug | `false` |

---

## Câu hỏi thường gặp

### Về hệ thống

**VietCare có khác gì so với ChatGPT hay các chatbot thông thường không?**

Có. ChatGPT là một LLM thuần — nó trả lời dựa trên kiến thức đã học trong quá trình huấn luyện, không có khả năng truy cập dữ liệu nội bộ của bạn theo thời gian thực. VietCare là một **Agent có kiến thức chuyên ngành**: kết hợp LLM với cơ sở dữ liệu y tế nội bộ (knowledge base) và các dịch vụ bên ngoài (OpenStreetMap), đồng thời tự quyết định khi nào cần dùng nguồn nào.

**"Agent" nghĩa là gì trong ngữ cảnh này?**

Một AI Agent là hệ thống có khả năng: (1) nhận mục tiêu, (2) lập kế hoạch hành động, (3) thực thi hành động thông qua các công cụ, (4) quan sát kết quả, (5) điều chỉnh và lặp lại. VietCare thực hiện vòng lặp này: LLM quyết định cần làm gì → hệ thống thực thi công cụ → kết quả được đưa lại cho LLM → LLM quyết định bước tiếp theo.

**Dữ liệu y tế trong knowledge base đến từ đâu?**

Knowledge base được xây dựng từ bộ dữ liệu FAQ sức khỏe tâm thần (Mental Health FAQ), có thể mở rộng bằng cách upload thêm file CSV/JSON qua API. Dữ liệu được lưu trong PostgreSQL và đánh chỉ mục bằng FAISS vector search để tìm kiếm ngữ nghĩa.

**Hệ thống có thể tư vấn y tế thay thế bác sĩ không?**

Không. VietCare cung cấp thông tin y tế tham khảo, không phải tư vấn y khoa chính thức. System prompt của agent luôn nhắc người dùng tham khảo bác sĩ với các triệu chứng nghiêm trọng. Đây là công cụ hỗ trợ tìm kiếm thông tin, không phải thay thế chuyên gia y tế.

---

### Về kỹ thuật

**Tại sao dùng OpenRouter thay vì OpenAI trực tiếp?**

OpenRouter là một API gateway hợp nhất cho phép gọi nhiều nhà cung cấp LLM (DeepSeek, GPT, Claude, Mistral, ...) qua cùng một interface tương thích OpenAI SDK. Điều này cho phép thay đổi mô hình mà không cần sửa code — chỉ cần thay giá trị `LLM_MODEL` trong file `.env`.

**FAISS là gì và tại sao dùng nó?**

FAISS (Facebook AI Similarity Search) là thư viện tìm kiếm vector hiệu năng cao. Khi người dùng hỏi, câu hỏi được chuyển thành vector số học (embedding), sau đó FAISS tìm nhanh các tài liệu có vector gần nhất về mặt ngữ nghĩa trong knowledge base. Đây là cơ chế RAG — lấy đúng thông tin liên quan trước khi gọi LLM để tránh ảo giác (hallucination).

**Vector store có cần rebuild khi restart server không?**

Không cần. Vector store được cache ở hai lớp: (1) in-memory dict trong `LLMService`, (2) file `.pkl` trên đĩa (trong `app/vector_stores/`, đã gitignore). Khi restart, hệ thống tự load từ đĩa nếu có, nếu không thì build lại từ database — quá trình này hoàn toàn tự động và trong suốt với người dùng.

**Tại sao file `.pkl` không có trong git repo?**

File vector store có thể lên đến hàng chục MB tùy kích thước knowledge base. Lưu trong git làm repo phình to và file sẽ lỗi thời mỗi khi dữ liệu DB thay đổi. Thay vào đó, `.pkl` được gitignore và tự build lại từ database khi cần — đảm bảo luôn đồng bộ với dữ liệu thực tế.

**Tại sao streaming dùng 2 giai đoạn thay vì stream thẳng?**

OpenAI Function Calling và streaming không hoạt động đồng thời một cách đơn giản: khi LLM cần gọi công cụ, phản hồi phải hoàn thành trước để hệ thống biết công cụ nào cần gọi. VietCare giải quyết bằng hai giai đoạn: (1) giải quyết toàn bộ tool calls bằng non-streaming call, (2) stream câu trả lời cuối sau khi đã có đủ context. Người dùng chỉ thấy văn bản streaming ra ở giai đoạn cuối.

**`MAX_ITERATIONS = 5` có ý nghĩa gì?**

Đây là cơ chế bảo vệ tránh vòng lặp vô hạn. Trong lý thuyết, agent có thể liên tục gọi công cụ rồi quyết định cần gọi thêm công cụ khác mà không dừng. Giới hạn 5 vòng đảm bảo hệ thống luôn trả về trong thời gian hợp lý. Với các câu hỏi thực tế, agent thường hoàn thành trong 1–2 vòng lặp.

**Làm sao để thêm công cụ mới vào Agent?**

Ba bước đơn giản:
1. Tạo file `app/services/tools/ten_tool.py` với `TEN_TOOL_SCHEMA` (JSON schema mô tả tham số) và hàm thực thi
2. Import và thêm schema vào danh sách `TOOLS` trong `app/services/agent_service.py`
3. Thêm nhánh xử lý trong method `_execute_tool()` của `AgentService`

Agent sẽ tự học cách dùng công cụ mới dựa trên phần mô tả (description) trong schema — không cần fine-tune hay chỉnh sửa prompt.

---

### Về vận hành

**Cần những API key nào để chạy?**

Bắt buộc: `OPENROUTER_API_KEY` để gọi LLM và thông tin đăng nhập PostgreSQL. Nominatim và Overpass API (cho tính năng tìm bệnh viện) hoàn toàn miễn phí, không cần key.

**Chi phí vận hành ước tính là bao nhiêu?**

Phụ thuộc vào mô hình LLM được chọn. Với `deepseek/deepseek-chat-v3.1:free` (mặc định), chi phí API bằng 0. Với các mô hình mạnh hơn như GPT-4o thì khoảng 0.01–0.03 USD mỗi câu hỏi. Nominatim và Overpass API miễn phí nhưng có rate limit — 1 request/giây với Nominatim theo chính sách sử dụng của OSM.

**Hệ thống có thể phục vụ nhiều người dùng đồng thời không?**

Có. FastAPI là async framework, xử lý các yêu cầu đồng thời tốt. Bottleneck chính là độ trễ API của LLM (thường 1–3 giây mỗi yêu cầu). Nếu cần mở rộng quy mô, có thể chạy nhiều instance đằng sau load balancer và dùng PostgreSQL connection pool (đã cấu hình trong `database.py`).

**Dữ liệu người dùng được lưu ở đâu?**

Toàn bộ lịch sử hội thoại và tin nhắn được lưu trong PostgreSQL. Mỗi tin nhắn được persist vào DB trước khi gọi LLM. Không có dữ liệu người dùng nào được gửi đến bên thứ ba ngoài nội dung câu hỏi/trả lời được truyền tới OpenRouter để xử lý.

---

## Giấy phép

MIT

## Tác giả

**Duy Nguyen**
- Email: duynvt.work@gmail.com
- LinkedIn: [linkedin.com/in/duynvt0203](https://www.linkedin.com/in/duynvt0203)
