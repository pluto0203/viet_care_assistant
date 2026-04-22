# VietCare Assistant 🏥

AI-powered Healthcare Q&A system with **RAG** (Retrieval-Augmented Generation), built with FastAPI.

> Ask health questions → AI retrieves relevant medical knowledge → generates accurate, cited answers.

## ✨ Key Features

- 🤖 **RAG-powered Q&A** — FAISS vector search + LLM for grounded, hallucination-resistant answers
- 💬 **Multi-turn Conversations** — context-aware follow-up questions  
- ⚡ **Streaming Responses** — Server-Sent Events (SSE) for real-time chat UX
- 🔐 **JWT Authentication** — secure user registration & login (Argon2 hashing)
- 📚 **Knowledge Base Management** — upload FAQ datasets, auto-build vector stores
- 🏥 **Health Checks** — liveness/readiness probes for production monitoring
- 🐳 **Docker Ready** — one-command deployment with `docker compose up`

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────────────────────────────────┐
│   Frontend   │     │              FastAPI Backend              │
│  (Streamlit) │────▶│                                          │
└──────────────┘     │  ┌────────┐  ┌─────────────┐  ┌──────┐  │
                     │  │ Router │─▶│   Service   │─▶│  DB  │  │
                     │  │ (HTTP) │  │  (Business) │  │(PgSQL)│  │
                     │  └────────┘  └──────┬──────┘  └──────┘  │
                     │                     │                    │
                     │              ┌──────▼──────┐             │
                     │              │  LLM Service │            │
                     │              │ ┌──────────┐ │            │
                     │              │ │  FAISS   │ │            │
                     │              │ │ (Vector) │ │            │
                     │              │ └──────────┘ │            │
                     │              │ ┌──────────┐ │            │
                     │              │ │ OpenRouter│ │            │
                     │              │ │  (LLM)   │ │            │
                     │              │ └──────────┘ │            │
                     │              └──────────────┘            │
                     └──────────────────────────────────────────┘
```

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **API Framework** | FastAPI (async, OpenAPI docs) |
| **Database** | PostgreSQL (Supabase) + SQLAlchemy 2.0 |
| **Auth** | JWT + Argon2 password hashing |
| **AI/ML** | LangChain, FAISS, HuggingFace Embeddings |
| **LLM Provider** | OpenRouter (DeepSeek, GPT, etc.) |
| **Config** | Pydantic Settings (validated at startup) |
| **Logging** | structlog (JSON in prod, colored in dev) |
| **DevOps** | Docker, Docker Compose, GitHub Actions |
| **Frontend** | Streamlit |

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone & configure
git clone https://github.com/pluto0203/viet_care_assistant.git
cd viet_care_assistant
cp .env.example .env  # Fill in your values

# Run
docker compose up --build
```

### Option 2: Local Development

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e ".[dev]"

# Configure
cp .env.example .env  # Fill in your API keys

# Run backend
uvicorn app.app_main:app --host 127.0.0.1 --port 18080 --reload

# Run frontend (separate terminal)
streamlit run app/frontend/app.py
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | GET | API info |
| `GET /health` | GET | Health check with dependency status |
| `POST /auth/register` | POST | Create user account |
| `POST /auth/login` | POST | Get JWT access token |
| `POST /chat/{id}/conversations` | POST | Create conversation |
| `POST /chat/{id}/conversations/{cid}/messages` | POST | Send message (sync) |
| `POST /chat/{id}/conversations/{cid}/stream` | POST | Send message (SSE streaming) |
| `POST /kb_faq/{id}/faqs/upload` | POST | Upload FAQ dataset |

Full interactive docs at: `http://localhost:18080/docs`

## 📂 Project Structure

```
vietcare-assistant/
├── app/
│   ├── app_main.py          # FastAPI entry point + middleware
│   ├── config.py             # Pydantic Settings
│   ├── database.py           # SQLAlchemy engine & session
│   ├── core/
│   │   ├── exceptions.py     # Custom exception hierarchy
│   │   └── logging.py        # Structured logging setup
│   ├── models/               # SQLAlchemy ORM models
│   ├── schemas/              # Pydantic request/response schemas
│   ├── router/               # HTTP route handlers (thin)
│   │   ├── auth.py
│   │   ├── chat.py
│   │   ├── health.py
│   │   ├── kb_collection.py
│   │   └── kb_faq.py
│   ├── services/             # Business logic layer
│   │   ├── auth.py
│   │   ├── chat_service.py
│   │   ├── llm.py
│   │   └── upload_faq.py
│   └── frontend/             # Streamlit UI
├── tests/                    # Unit & integration tests
├── data/                     # FAQ datasets
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `user` | ✅ | Database username |
| `password` | ✅ | Database password |
| `host` | ✅ | Database host |
| `port` | ❌ | Database port (default: 5432) |
| `dbname` | ✅ | Database name |
| `SECRET_KEY` | ✅ | JWT signing key |
| `OPENROUTER_API_KEY` | ✅ | OpenRouter API key |
| `LLM_MODEL` | ❌ | LLM model (default: deepseek) |
| `DEBUG` | ❌ | Debug mode (default: false) |

## 📄 License

MIT

## 👤 Author

**Duy Nguyen**  
📧 duynvt.work@gmail.com  
🔗 [LinkedIn](https://www.linkedin.com/in/duynvt0203)
