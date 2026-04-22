# app/services/chat_service.py
"""
Chat Service — business logic layer for conversations and messaging.
Keeps routers thin (HTTP only) and services testable (no HTTP dependency).
"""
from sqlalchemy.orm import Session

from app.models import Conversation as ConversationORM, Message as MessageORM, KBCollection
from app.services.llm import LLMService
from app.core.exceptions import CollectionNotFound, ConversationNotFound
from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatService:
    """
    Handles conversation creation, message persistence, and LLM interaction.
    Router delegates all business logic here.
    """

    def __init__(self, db: Session, llm_service: LLMService):
        self.db = db
        self.llm = llm_service

    # ── Validation Helpers ──

    def _validate_collection(self, collection_id: int) -> KBCollection:
        collection = (
            self.db.query(KBCollection)
            .filter(KBCollection.collection_id == collection_id)
            .first()
        )
        if not collection:
            raise CollectionNotFound(collection_id)
        return collection

    def _validate_conversation(self, conversation_id: int) -> ConversationORM:
        conversation = (
            self.db.query(ConversationORM)
            .filter(ConversationORM.conversation_id == conversation_id)
            .first()
        )
        if not conversation:
            raise ConversationNotFound(conversation_id)
        return conversation

    # ── Conversation Management ──

    def create_conversation(self, collection_id: int, userid: int, topic: str) -> ConversationORM:
        """Create a new conversation within a collection."""
        self._validate_collection(collection_id)

        conversation = ConversationORM(userid=userid, topic=topic)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)

        logger.info(
            "conversation_created",
            conversation_id=conversation.conversation_id,
            collection_id=collection_id,
        )
        return conversation

    # ── Messaging ──

    def _get_conversation_history(self, conversation_id: int, limit: int = 10) -> list[MessageORM]:
        """Fetch recent messages for multi-turn context."""
        return (
            self.db.query(MessageORM)
            .filter(MessageORM.conversation_id == conversation_id)
            .order_by(MessageORM.message_id.desc())
            .limit(limit)
            .all()
        )[::-1]  # Reverse to chronological order

    def send_message(
        self,
        collection_id: int,
        conversation_id: int,
        content: str,
        role: str = "user",
    ) -> MessageORM:
        """
        Process a user message:
        1. Validate collection & conversation exist
        2. Save user message
        3. Fetch conversation history for multi-turn context
        4. Call RAG + LLM
        5. Save and return assistant response
        """
        self._validate_collection(collection_id)
        self._validate_conversation(conversation_id)

        # Save user message
        user_message = MessageORM(
            conversation_id=conversation_id,
            role=role,
            content=content,
        )
        self.db.add(user_message)
        self.db.flush()

        if role != "user":
            self.db.commit()
            self.db.refresh(user_message)
            return user_message

        # Get conversation history for multi-turn context
        history = self._get_conversation_history(conversation_id)

        # Call RAG + LLM
        rag_response = self.llm.get_response(
            query=content,
            collection_id=collection_id,
            db=self.db,
            history=history,
        )

        # Save assistant response
        assistant_message = MessageORM(
            conversation_id=conversation_id,
            role="assistant",
            content=rag_response["text"],
        )
        self.db.add(assistant_message)
        self.db.commit()
        self.db.refresh(assistant_message)

        logger.info(
            "message_processed",
            conversation_id=conversation_id,
            collection_id=collection_id,
        )
        return assistant_message

    def stream_message(
        self,
        collection_id: int,
        conversation_id: int,
        content: str,
    ):
        """
        Stream a response using Server-Sent Events.
        Yields text chunks, then saves the full response.
        Returns a generator of text chunks and a callback to save.
        """
        self._validate_collection(collection_id)
        self._validate_conversation(conversation_id)

        # Save user message
        user_message = MessageORM(
            conversation_id=conversation_id,
            role="user",
            content=content,
        )
        self.db.add(user_message)
        self.db.flush()

        # Get history
        history = self._get_conversation_history(conversation_id)

        # Stream from LLM
        full_response = []
        for chunk in self.llm.get_streaming_response(
            query=content,
            collection_id=collection_id,
            db=self.db,
            history=history,
        ):
            full_response.append(chunk)
            yield chunk

        # Save complete response after streaming
        assistant_message = MessageORM(
            conversation_id=conversation_id,
            role="assistant",
            content="".join(full_response),
        )
        self.db.add(assistant_message)
        self.db.commit()

        logger.info(
            "stream_message_complete",
            conversation_id=conversation_id,
            response_len=len("".join(full_response)),
        )
