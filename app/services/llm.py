import os
import pickle
import json
import logging
from openai import OpenAI
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
from sqlalchemy.orm import Session
from app.config import config
from app.models import KBFAQ
from typing import Dict, List
from langchain_huggingface import HuggingFaceEmbeddings


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Khởi tạo client OpenAI với OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=config.OPENROUTER_API_KEY,
)


prompt_template = """
You are a healthcare assistant. Use the information from the knowledge base below to answer the question. If no relevant information is found, provide a general answer but prioritize the knowledge base.
Knowledge base: {context}
Question: {question}
Provide a concise and helpful answer in English.
"""

# Initialize the embedding model
embedder = HuggingFaceEmbeddings(model_name='all-MiniLM-L6-v2')

def build_or_load_vector_store(db: Session, collection_id: int) -> FAISS:
    """
    Xây dựng hoặc tải vector store từ bảng kb_faq cho collection_id cụ thể.
    """
    try:
        cache_path = f"{config.VECTOR_STORE_PATH}_collection_{collection_id}.pkl"
        if os.path.exists(cache_path):
            logger.info(f"Loading vector store from cache for collection {collection_id}")
            with open(cache_path, "rb") as f:
                return pickle.load(f)

        logger.info(f"Building new vector store for collection {collection_id}")
        faqs = db.query(KBFAQ).filter(KBFAQ.collection_id == collection_id).all()
        if not faqs:
            logger.warning(f"No FAQs found in collection {collection_id}")
            # Tạo vector store rỗng với embedding_function
            return FAISS.from_texts([""], embedding=embedder)

        docs = [
            Document(
                page_content=f.question + "\n" + f.answer,
                metadata={"faq_id": f.faq_id, "ext_id": f.ext_id or "", "collection_id": f.collection_id}
            ) for f in faqs
        ]
        vector_store = FAISS.from_documents(docs, embedding=embedder)

        with open(cache_path, "wb") as f:
            pickle.dump(vector_store, f)

        return vector_store
    except Exception as e:
        logger.error(f"Error building vector store for collection {collection_id}: {str(e)}")
        raise
def invalidate_cache(collection_id: int):
    """
    Xóa cache vector store cho collection_id cụ thể.
    """
    try:
        cache_path = f"{config.VECTOR_STORE_PATH}_collection_{collection_id}.pkl"
        if os.path.exists(cache_path):
            os.remove(cache_path)
            logger.info(f"Vector store cache invalidated for collection {collection_id}")
    except Exception as e:
        logger.error(f"Error invalidating cache: {str(e)}")
        raise

def get_response(query: str, collection_id: int, db: Session) -> Dict[str, any]:
    """
    Truy vấn RAG để trả lời câu hỏi dựa trên FAQ trong collection_id.
    """
    try:
        # Lấy vector store
        vector_store = build_or_load_vector_store(db, collection_id)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        # Tìm kiếm FAQ liên quan
        docs = retriever.invoke(query)
        context = "\n\n".join([doc.page_content for doc in docs])

        # Tạo prompt
        prompt = prompt_template.format(context=context, question=query)

        # Gọi LLM qua OpenRouter
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat-v3.1:free",
            messages=[
                {"role": "system", "content": "You are a healthcare assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        answer = response.choices[0].message.content

        # Tạo sources theo định dạng schema Message
        sources = [
            {"url": f"faq://{doc.metadata['faq_id']}", "title": f"FAQ {doc.metadata['ext_id']}"}
            for doc in docs
        ]

        logger.info(f"Query: {query}, Collection: {collection_id}, Sources: {sources}")
        return {"text": answer, "sources": sources}
    except Exception as e:
        logger.error(f"LLM/RAG error for collection {collection_id}: {str(e)}")
        raise ValueError(f"LLM/RAG error: {str(e)}")