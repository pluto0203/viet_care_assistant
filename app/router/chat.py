# app/router/chat.py
"""
Chat Router — thin HTTP adapter.
All business logic lives in ChatService.
"""
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.conversation import Conversation as ConversationOut, ConversationCreate
from app.schemas.message import Message as MessageOut, MessageCreate
from app.services.chat_service import ChatService
from app.services.llm import get_llm_service, LLMService
from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


def _get_chat_service(
    db: Session = Depends(get_db),
    llm: LLMService = Depends(get_llm_service),
) -> ChatService:
    """Dependency: inject ChatService with its dependencies."""
    return ChatService(db=db, llm_service=llm)


@router.post("/{collection_id}/conversations", response_model=ConversationOut)
async def create_conversation(
    collection_id: int,
    conversation: ConversationCreate,
    service: ChatService = Depends(_get_chat_service),
):
    """Create a new conversation for a knowledge base collection."""
    try:
        return service.create_conversation(
            collection_id=collection_id,
            userid=conversation.userid,
            topic=conversation.topic,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{collection_id}/conversations/{conversation_id}/messages",
    response_model=MessageOut,
)
async def send_message(
    collection_id: int,
    conversation_id: int,
    message: MessageCreate,
    service: ChatService = Depends(_get_chat_service),
):
    """Send a message and receive an AI response (non-streaming)."""
    try:
        return service.send_message(
            collection_id=collection_id,
            conversation_id=conversation_id,
            content=message.content,
            role=message.role,
        )
    except AppException as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.post(
    "/{collection_id}/conversations/{conversation_id}/stream",
)
async def stream_message(
    collection_id: int,
    conversation_id: int,
    message: MessageCreate,
    service: ChatService = Depends(_get_chat_service),
):
    """
    Send a message and receive a streaming AI response (Server-Sent Events).
    Frontend consumes this with EventSource or fetch + ReadableStream.
    """
    def event_generator():
        try:
            for chunk in service.stream_message(
                collection_id=collection_id,
                conversation_id=conversation_id,
                content=message.content,
            ):
                yield f"data: {json.dumps({'text': chunk})}\n\n"
            yield f"data: {json.dumps({'done': True})}\n\n"
        except AppException as e:
            yield f"data: {json.dumps({'error': e.message})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )