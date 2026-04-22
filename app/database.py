# app/database.py
"""
Database engine and session management.
Uses SQLAlchemy 2.0 DeclarativeBase pattern.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import config


engine = create_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models (SQLAlchemy 2.0 style)."""
    pass


def get_db():
    """
    Dependency that provides a database session per request.
    Automatically closes the session when the request finishes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
