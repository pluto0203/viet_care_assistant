# app/config.py
from dotenv import load_dotenv
from pathlib import Path
import logging
import os
from sqlalchemy import create_engine, NullPool


# Trỏ tuyệt đối tới .env ở THƯ MỤC GỐC PROJECT (cùng cấp main.py)
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
load_dotenv(dotenv_path=ENV_PATH)




class Config:
    USER = os.getenv("user")
    PASSWORD = os.getenv("password")
    HOST = os.getenv("host")
    PORT = os.getenv("port")
    DBNAME = os.getenv("dbname")

    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE_URL = f"postgresql+psycopg2://{USER}:{PASSWORD}@{HOST}:{PORT}/{DBNAME}?sslmode=require"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15


    # def validate(self):
    #     # logging.basicConfig()
    #     # logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    #     # print(f"Database URL: {self.DATABASE_URL}")
    #     engine = create_engine(self.DATABASE_URL, poolclass=NullPool)
    #     try:
    #         with engine.connect() as connection:
    #             print("Connection successful!")
    #     except Exception as e:
    #         print(f"Failed to connect: {e}")


config = Config()
