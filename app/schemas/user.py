#app/schemas/user.py
from datetime import date
from enum import Enum

from pydantic import BaseModel, EmailStr

class Role(str, Enum):
    ADMIN = "admin"
    USER = "user"
    ADVISOR = "advisor"

class UserCreate(BaseModel):
    username: str
    password: str
    role: Role
    date_of_birth: date
    phone_number: str
    email: EmailStr

class UserOut(BaseModel):
    userid: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

