#app/router/chat.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.models import Conversation as ConversationORM, Message as MessageORM, KBCollection
from app.schemas.conversation import Conversation as ConversationOut, ConversationCreate
from app.schemas.message import Message as MessageOut, MessageCreate

from app.services.llm import get_response
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/{collection_id}/conversations", response_model=ConversationOut)
async def create_conversation(
        collection_id: int,
        conversation: ConversationCreate,
        db: Session = Depends(get_db)
):
    """
    Tạo một conversation mới cho collection_id.
    """
    try:
        db_collection = db.query(KBCollection).filter(KBCollection.collection_id == collection_id).first()
        if not db_collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        db_conversation = ConversationORM(
            userid=conversation.userid,
            topic=conversation.topic
        )
        db.add(db_conversation)
        db.commit()
        db.refresh(db_conversation)
        logger.info(f"Created conversation: {db_conversation.conversation_id} for collection {collection_id}")
        return db_conversation
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error creating conversation: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e

@router.post("/{collection_id}/conversations/{conversation_id}/messages", response_model=MessageOut)
async def send_message(
        collection_id: int,
        conversation_id: int,
        message: MessageCreate,
        db: Session = Depends(get_db)
):
    """
    Gửi tin nhắn và nhận phản hồi từ LLM với RAG.
    """
    try:
        # Kiểm tra collection_id và conversation_id
        db_collection = db.query(KBCollection).filter(KBCollection.collection_id == collection_id).first()
        if not db_collection:
            raise HTTPException(status_code=404, detail="Collection not found")

        db_conversation = db.query(ConversationORM).filter(ConversationORM.conversation_id == conversation_id).first()
        if not db_conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Lưu tin nhắn người dùng
        user_message = MessageORM(
            conversation_id=conversation_id,
            role=message.role,
            content=message.content
        )
        db.add(user_message)
        db.flush()
        logger.info(f"Sent message: {user_message.content} for conversation: {conversation_id}")

        # Gọi RAG để lấy phản hồi nếu là tin nhắn người dùng
        if message.role == "user":
            rag_response = get_response(message.content, collection_id, db)
            assistant_message = MessageORM(
                conversation_id = conversation_id,
                role = "assistant",
                content = rag_response["text"],
            )
            db.add(assistant_message)
            db.commit()
            db.refresh(assistant_message)

            logger.info(f"Sent message and received response for conversation {conversation_id}")
            return assistant_message
        else:
            db.commit()
            db.refresh(user_message)
            logger.info(f"Sent message for conversation {conversation_id}")
            return user_message
    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Error sending message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error") from e