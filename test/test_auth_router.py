import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate, Role, Token
from app.services.auth import get_password_hash, verify_password, create_access_token
from app.router.auth import register, login
from unittest.mock import MagicMock
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordRequestForm
from app.config import config
from jose import jwt

@pytest.mark.asyncio
async def test_register_new_user():
    # Mock database session
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None  # No existing user

    # Test user data
    user_data = UserCreate(
        username= "testuser",
        password= "testpassword",
        role= Role.USER,
        date_of_birth= datetime(2003, 12, 17),
        phone= "0853781712",
        email= "testuser@example.com",
    )

    # Call register
    result = register(user_data, db)

    # Assertions
    assert result.username == "testuser"
    assert result.email == "testuser@example.com"
    db.add.assert_called()
    db.commit.assert_called()
    db.refresh.assert_called()

@pytest.mark.asyncio
async def test_register_existing_user():
    # Mock database session with existing user
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = User(username="testuser")

    # Test user data
    user_data = UserCreate(
        username="testuser",
        password="testpassword",
        role=Role.USER,
        date_of_birth=datetime(2003, 12, 17),
        phone="0853781712",
        email="testuser@example.com",
    )

    # Expect HTTPException
    with pytest.raises(HTTPException) as exc:
        register(user_data, db)
    assert exc.value.status_code == 400
    assert exc.value.detail == "User Name already registered!"

@pytest.mark.asyncio
async def test_login_success():
    # Mock database session
    db = MagicMock(spec=Session)
    hashed_password = get_password_hash("testpassword")
    mock_user = User(
        username="testuser",
        hashed_password=hashed_password,
        role=Role.USER,
        date_of_birth=datetime(2003, 12, 17),
        phone="0853781712",
        email="testuser@example.com",
    )
    db.query.return_value.filter.return_value.first.return_value = mock_user

    # Mock form data
    form_data = MagicMock(spec=OAuth2PasswordRequestForm)
    form_data.username = "testuser"
    form_data.password = "testpassword"

    # Call login
    result = login(form_data, db)

    # Assertions
    assert "access_token" in result
    assert result["token_type"] == "bearer"
    decoded = jwt.decode(result["access_token"], config.SECRET_KEY, algorithms=["HS256"])
    assert decoded["sub"] == "testuser"

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    # Mock database session
    db = MagicMock(spec=Session)
    db.query.return_value.filter.return_value.first.return_value = None  # No user

    # Mock form data
    form_data = MagicMock(spec=OAuth2PasswordRequestForm)
    form_data.username = "testuser"
    form_data.password = "testpassword"

    # Expect HTTPException
    with pytest.raises(HTTPException) as exc:
        login(form_data, db)
    assert exc.value.status_code == 401
    assert exc.value.detail == "Incorrect username or password"