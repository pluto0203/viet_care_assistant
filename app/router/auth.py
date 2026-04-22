# app/router/auth.py
"""
Authentication Router — register & login endpoints.
Uses custom exceptions for clean error handling.
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import timedelta

from app.database import get_db
from app.models.user import User, Roles
from app.schemas.user import UserOut, UserCreate, Token
from app.services.auth import get_password_hash, verify_password, create_access_token
from app.config import config
from app.core.exceptions import DuplicateUser, InvalidCredentials
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    try:
        # Check for existing user
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise DuplicateUser(user.username)

        # Create user with hashed password
        new_user = User(
            username=user.username,
            role=user.role,
            date_of_birth=user.date_of_birth,
            phone=user.phone,
            email=user.email,
            hashed_password=get_password_hash(user.password),
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        logger.info("user_registered", username=user.username)
        return new_user

    except DuplicateUser as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("registration_db_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")


@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticate user and return JWT access token."""
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise InvalidCredentials()

        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        logger.info("user_logged_in", username=user.username)
        return {"access_token": access_token, "token_type": "bearer"}

    except InvalidCredentials as e:
        raise HTTPException(
            status_code=e.status_code,
            detail=e.message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    except SQLAlchemyError as e:
        db.rollback()
        logger.error("login_db_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal Server Error")
