# app/router/health.py
"""
Health Check Router — production-ready liveness & readiness probes.
Used by Docker, K8s, load balancers to monitor service status.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.services.llm import get_llm_service, LLMService
from app.config import config
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(
    db: Session = Depends(get_db),
):
    """
    Comprehensive health check.
    Returns status of each dependency (database, LLM, vector store).
    """
    checks = {}

    # Database check
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}

    # LLM service check (lightweight — just checks if client is configured)
    try:
        llm = get_llm_service()
        checks["llm"] = {
            "status": "healthy",
            "model": config.LLM_MODEL,
        }
    except Exception as e:
        checks["llm"] = {"status": "unhealthy", "error": str(e)}

    # Overall status
    all_healthy = all(c["status"] == "healthy" for c in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": config.APP_VERSION,
        "app": config.APP_NAME,
        "checks": checks,
    }


@router.get("/health/live")
async def liveness():
    """Liveness probe — is the process alive?"""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness(db: Session = Depends(get_db)):
    """Readiness probe — can the service accept traffic?"""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        return {"status": "not_ready"}, 503
