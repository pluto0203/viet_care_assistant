# app/main.py
from fastapi import FastAPI
from sqlalchemy import create_engine
from app.config import Config
from app.router import kb_faq

app = FastAPI()
app.include_router(kb_faq.router)

@app.on_event("startup")
def on_startup():
    config = Config()
    engine = create_engine(config.DATABASE_URL)
    # bootstrap_database(engine)