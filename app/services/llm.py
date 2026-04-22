# app/services/llm.py
"""
LLM & RAG Service — handles vector store management, retrieval, and LLM calls.
Supports both regular and streaming responses.
"""
import os
import pickle
import json
from typing import Dict, List, AsyncGenerator

from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from sqlalchemy.orm import Session
from langchain_huggingface import HuggingFaceEmbeddings

from app.config import config
from app.models import KBFAQ
from app.core.exceptions import LLMServiceError, VectorStoreError
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── System Prompts ──

SYSTEM_PROMPT = (
    "You are VietCare Assistant — a professional, empathetic healthcare AI. "
    "You provide evidence-based health information in a clear, easy-to-understand manner. "
    "Always recommend consulting a doctor for serious symptoms. "
    "Respond in the same language as the user's question."
)

RAG_PROMPT_TEMPLATE = """Use the following knowledge base context to answer the question.
If the context is relevant, base your answer on it. If not, provide a general but helpful answer.
Always cite which FAQ sources you used.

Context from knowledge base:
{context}

Question: {question}

Provide a concise, helpful, and empathetic answer."""


class LLMService:
    """
    Encapsulates all LLM and RAG operations.
    Single Responsibility: manage embeddings, vector store, and LLM calls.
    """

    def __init__(self):
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.OPENROUTER_API_KEY,
        )
        self.embedder = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
        self._vector_store_cache: Dict[int, FAISS] = {}
        logger.info("llm_service_initialized", model=config.LLM_MODEL)

    # ── Vector Store Management ──

    def build_or_load_vector_store(self, db: Session, collection_id: int) -> FAISS:
        """Build or load FAISS vector store for a collection."""
        # Check in-memory cache first
        if collection_id in self._vector_store_cache:
            return self._vector_store_cache[collection_id]

        try:
            # Check disk cache
            cache_path = os.path.join(
                config.VECTOR_STORE_PATH, f"collection_{collection_id}.pkl"
            )
            if os.path.exists(cache_path):
                logger.info("vector_store_loaded_from_disk", collection_id=collection_id)
                with open(cache_path, "rb") as f:
                    vs = pickle.load(f)
                self._vector_store_cache[collection_id] = vs
                return vs

            # Build from database
            logger.info("vector_store_building", collection_id=collection_id)
            faqs = db.query(KBFAQ).filter(KBFAQ.collection_id == collection_id).all()

            if not faqs:
                logger.warning("no_faqs_found", collection_id=collection_id)
                vs = FAISS.from_texts([""], embedding=self.embedder)
                self._vector_store_cache[collection_id] = vs
                return vs

            docs = [
                Document(
                    page_content=f"{faq.question}\n{faq.answer}",
                    metadata={
                        "faq_id": faq.faq_id,
                        "ext_id": faq.ext_id or "",
                        "collection_id": faq.collection_id,
                    },
                )
                for faq in faqs
            ]
            vs = FAISS.from_documents(docs, embedding=self.embedder)

            # Persist to disk
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "wb") as f:
                pickle.dump(vs, f)

            self._vector_store_cache[collection_id] = vs
            logger.info("vector_store_built", collection_id=collection_id, num_docs=len(docs))
            return vs

        except Exception as e:
            logger.error("vector_store_error", collection_id=collection_id, error=str(e))
            raise VectorStoreError(f"Failed to build vector store: {e}")

    def invalidate_cache(self, collection_id: int) -> None:
        """Clear both in-memory and disk cache for a collection."""
        self._vector_store_cache.pop(collection_id, None)
        cache_path = os.path.join(
            config.VECTOR_STORE_PATH, f"collection_{collection_id}.pkl"
        )
        if os.path.exists(cache_path):
            os.remove(cache_path)
            logger.info("cache_invalidated", collection_id=collection_id)

    # ── Retrieval ──

    def _retrieve_context(self, query: str, db: Session, collection_id: int) -> tuple[str, list]:
        """Retrieve relevant documents from vector store."""
        vector_store = self.build_or_load_vector_store(db, collection_id)
        retriever = vector_store.as_retriever(search_kwargs={"k": config.RAG_TOP_K})
        docs = retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in docs])
        sources = [
            {"url": f"faq://{doc.metadata['faq_id']}", "title": f"FAQ {doc.metadata['ext_id']}"}
            for doc in docs
        ]
        return context, sources

    def _build_messages(
        self,
        query: str,
        context: str,
        history: list = None,
    ) -> list[dict]:
        """Build the message list for the LLM call, including conversation history."""
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        # Add conversation history for multi-turn context
        if history:
            for msg in history[-config.MAX_HISTORY_MESSAGES:]:
                messages.append({"role": msg.role, "content": msg.content})

        # Add current query with RAG context
        prompt = RAG_PROMPT_TEMPLATE.format(context=context, question=query)
        messages.append({"role": "user", "content": prompt})

        return messages

    # ── LLM Calls ──

    def get_response(
        self,
        query: str,
        collection_id: int,
        db: Session,
        history: list = None,
    ) -> Dict[str, any]:
        """
        RAG-augmented LLM response (non-streaming).
        Returns: {"text": "...", "sources": [...]}
        """
        try:
            context, sources = self._retrieve_context(query, db, collection_id)
            messages = self._build_messages(query, context, history)

            response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
            )
            answer = response.choices[0].message.content

            logger.info(
                "llm_response",
                collection_id=collection_id,
                query_len=len(query),
                answer_len=len(answer),
                num_sources=len(sources),
            )
            return {"text": answer, "sources": sources}

        except Exception as e:
            logger.error("llm_error", error=str(e), collection_id=collection_id)
            raise LLMServiceError(f"LLM call failed: {e}")

    def get_streaming_response(
        self,
        query: str,
        collection_id: int,
        db: Session,
        history: list = None,
    ):
        """
        RAG-augmented LLM response with streaming (generator).
        Yields text chunks as they arrive from the LLM.
        """
        try:
            context, sources = self._retrieve_context(query, db, collection_id)
            messages = self._build_messages(query, context, history)

            stream = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True,
            )

            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error("llm_stream_error", error=str(e))
            raise LLMServiceError(f"LLM streaming failed: {e}")

    def check_health(self) -> bool:
        """Check if LLM service is reachable."""
        try:
            self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=5,
            )
            return True
        except Exception:
            return False


# ── Singleton Instance ──
# Used via dependency injection in routers

_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Lazy singleton — initialized on first use."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service