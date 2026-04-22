# tests/conftest.py
"""
Shared test fixtures.
Provides test database sessions, FastAPI test client, and mock services.
"""
import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from sqlalchemy import create_engine, NullPool, StaticPool
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.app_main import app
from app.models.user import User, Roles
from app.services.auth import get_password_hash


# ── In-memory SQLite for fast tests ──

SQLALCHEMY_TEST_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_TEST_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Fresh database session per test — tables created and dropped."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """FastAPI test client with overridden DB dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session):
    """Pre-created test user for auth tests."""
    user = User(
        username="testuser",
        hashed_password=get_password_hash("testpass123"),
        role=Roles.USER,
        date_of_birth=datetime(1995, 1, 1).date(),
        phone="+84123456789",
        email="test@example.com",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(client, test_user):
    """JWT auth headers for authenticated requests."""
    response = client.post(
        "/auth/login",
        data={"username": "testuser", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def mock_llm_service():
    """Mocked LLM service — no real API calls in tests."""
    with patch("app.services.llm.get_llm_service") as mock:
        service = MagicMock()
        service.get_response.return_value = {
            "text": "This is a test response from the AI.",
            "sources": [{"url": "faq://1", "title": "FAQ TEST-001"}],
        }
        service.check_health.return_value = True
        mock.return_value = service
        yield service
