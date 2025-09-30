#app/router/auth
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import SQLAlchemyError

from app.schemas.user import UserOut, UserCreate, Token
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm  import Session
from app.database import get_db
from app.models.user import User, Roles
from app.services.auth import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.config import config


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags= ["auth"])

@router.post("/register", response_model=UserOut)
def register(user: UserCreate, db: Session= Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.username == user.username).first()
        if db_user:
            raise HTTPException(status_code=400, detail= "User Name already registered!")
        hashed_password = get_password_hash(user.password)
        new_user = User(
            username = user.username,
            role = user.role,
            date_of_birth = user.date_of_birth,
            phone= user.phone,
            email = user.email,
            hashed_password= hashed_password
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"New user is registered: {user.username}")
        return new_user
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Registration database ERROR!")
        raise HTTPException(status_code=500, detail= "Internal Server Error") from e


@router.post("/login", response_model= Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code= status.HTTP_401_UNAUTHORIZED,
                detail= "Incorrect username or password",
                headers= {"WWW-Authenticate": "Bearer"}
            )

        access_token_expires = timedelta(minutes= config.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(data={"sub": user.username},
                                           expires_delta= access_token_expires)
        logger.info(f"User logged in: {user.username}")
        return {"access_token": access_token, "token_type": "bearer"}

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Registration database ERROR!")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e

