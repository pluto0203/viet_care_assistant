# app/app_main.py
"""
Application entry point.
- Global exception handler for AppException
- CORS middleware
- Centralized logging setup
- Lifespan for startup/shutdown
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.config import config
from app.database import engine, Base
from app.router import auth, chat, kb_collection, kb_faq
from app.router.health import router as health_router
from app.core.exceptions import AppException
from app.core.logging import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # ── Startup ──
    setup_logging(debug=config.DEBUG)
    logger = get_logger("app")

    Base.metadata.create_all(bind=engine)
    logger.info(
        "app_started",
        app=config.APP_NAME,
        version=config.APP_VERSION,
        debug=config.DEBUG,
    )
    yield
    # ── Shutdown ──
    logger.info("app_shutdown")


app = FastAPI(
    title=config.APP_NAME,
    version=config.APP_VERSION,
    description="AI-powered Healthcare Q&A with RAG (Retrieval-Augmented Generation)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)


# ── Middleware ──

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global Exception Handler ──

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    """
    Catch all custom AppExceptions and return consistent JSON error responses.
    This means services can raise domain exceptions without importing FastAPI.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "detail": exc.detail,
        },
    )


# ── Routers ──

app.include_router(health_router)
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(kb_faq.router)
app.include_router(kb_collection.router)


# ── Root ──

@app.get("/", tags=["root"])
async def root():
    return {
        "app": config.APP_NAME,
        "version": config.APP_VERSION,
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.app_main:app",
        host="127.0.0.1",
        port=18080,
        reload=config.DEBUG,
    )
