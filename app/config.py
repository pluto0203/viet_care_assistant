from dotenv import load_dotenv
from pathlib import Path
import os

load_dotenv()

class Config:
    OPEN_API_KEY = os.getenv("OPEN_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_URL = os.getenv("DATABASE_URL")
    ACCESS_TOKEN_EXPRIE_MINUTES = 30

config = Config()