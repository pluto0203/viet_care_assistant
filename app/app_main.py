# app/app_main.py
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import engine, Base
from app.router import auth, chat, kb_collection, kb_faq


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)




@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)   # tạo bảng lần đầu (sync OK)
    # any_startup_init_if_needed()
    logger.info("Application started")
    yield
    # Shutdown (nếu cần đóng tài nguyên)
    logger.info("Application shutdown")

app = FastAPI(title="Mini Vietnamese Care Assistant", lifespan=lifespan)

# 2) Mount routers
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(kb_faq.router)
app.include_router(kb_collection.router)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=18080)
