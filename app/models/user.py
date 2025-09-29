# app/models/user.py
from sqlalchemy import Column, Integer, String, Enum, DATE
from sqlalchemy.orm import relationship

from app.database import Base
import enum

class Roles(enum.Enum):
    ADMIN = "admin"
    USER = "user"
    ADVISOR = "advisor"

class User(Base):
    __tablename__ = "users"
    userid = Column("UserID", Integer, primary_key=True, index=True, autoincrement=True)
    username = Column("UserName", String(50), unique=True, index=True, nullable=False)  # NVARCHAR -> String
    role = Column("Role", Enum(Roles, name="roles_enum"), nullable=False)
    date_of_birth = Column("DOB", DATE, nullable=False)
    phone = Column("PhoneNum", String(15), nullable=False)                               # NVARCHAR -> String
    email = Column("Email", String(255), unique=True, index=True, nullable=False)
    hashed_password = Column("HashedPassword", String(255), nullable=False)

    #Nguoc: 1 user -> N conversations
    conversation= relationship(
        "Conversation",
        back_populates= "user",
        cascade="all, delete-orphan"
    )

