# app/models/user.py
from sqlalchemy import Column, Integer, String, Enum, DATE
from app.database import Base
import enum

class Roles(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    ADVISOR = "advisor"

class User(Base):
    __tablename__ = "users"
    UserID = Column(Integer, primary_key=True, index=True, autoincrement=True)
    UserName = Column(String(50), unique=True, index=True, nullable=False)  # NVARCHAR -> String
    Role = Column(Enum(Roles, name="roles_enum"), nullable=False)
    DOB = Column(DATE, nullable=False)
    Phone = Column(String(15), nullable=False)                               # NVARCHAR -> String
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
