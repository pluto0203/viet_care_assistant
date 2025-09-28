import pytest
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy import create_engine, NullPool
from sqlalchemy.orm import sessionmaker
import app.services.auth as auth_mod
import app.models

from app.services.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.config import Config
from app.models.user import User, Roles
from app.models.message import Message
from app.models.conversation import Conversation
from app.database import Base

config = Config()
TEST_DATABASE_URL = config.DATABASE_URL
engine = create_engine(TEST_DATABASE_URL, poolclass=NullPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Base.metadata.drop_all(bind=engine)

# Các test sync: KHÔNG cần async/await
def test_get_password_hash():
    password = "pluto@123"
    hashed_password = get_password_hash(password)
    assert hashed_password != password
    assert verify_password(password, hashed_password) is True

def test_verify_password():
    password = "pluto@123"
    hashed_password = get_password_hash(password)
    assert verify_password(password, hashed_password) is True
    assert verify_password("wrongpassword", hashed_password) is False

def test_create_access_token():
    data = {"sub": "testuser"}
    token = create_access_token(data, expires_delta=timedelta(minutes=15))
    decoded = jwt.decode(token, config.SECRET_KEY, algorithms=["HS256"])
    assert decoded["sub"] == "testuser"
    assert "exp" in decoded
    assert isinstance(decoded["exp"], int)

# Các test cần await: đánh dấu asyncio (yêu cầu pytest-asyncio)
@pytest.mark.asyncio
async def test_get_current_user_valid_token(db_session, monkeypatch):
    monkeypatch.setattr(auth_mod, "SessionLocal", TestingSessionLocal, raising=True)
    print(engine.url)
    hashed_password = get_password_hash("testpassword")
    test_user = User(
        UserID = int(1001),
        UserName="testuser",
        hashed_password=hashed_password,
        Role=Roles.USER,
        DOB=datetime(1990, 1, 1).date(),
        Phone="+0853781712",
        email="testuser@example.com",
    )
    db_session.add(test_user)
    db_session.commit()
    #db_session.refresh(test_user)

    token = create_access_token({"sub": "testuser"})
    user = await get_current_user(token=token)
    assert user.UserName == "testuser"
    assert user.email == "testuser@example.com"

@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session, monkeypatch):
    monkeypatch.setattr(auth_mod, "SessionLocal", TestingSessionLocal, raising=True)

    with pytest.raises(Exception) as exc:
        await get_current_user(token="invalid_token")
    # Tùy implement, thường raise HTTPException 401
    assert getattr(exc.value, "status_code", 401) == 401

@pytest.mark.asyncio
async def test_get_current_user_nonexistent_user(db_session, monkeypatch):
    monkeypatch.setattr(auth_mod, "SessionLocal", TestingSessionLocal, raising=True)
    token = create_access_token({"sub": "nonexistent_user"})
    with pytest.raises(Exception) as exc:
        await get_current_user(token=token)
    assert getattr(exc.value, "status_code", 401) == 401
