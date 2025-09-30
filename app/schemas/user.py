#app/schemas/user.py
from datetime import date
from enum import Enum
from app.models import Roles

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    password: str
    role: Roles
    date_of_birth: date
    phone: str
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

