# app/services/tools/kb_tool.py
from sqlalchemy.orm import Session
from app.services.llm import LLMService

KB_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_knowledge_base",
        "description": (
            "Tìm kiếm thông tin y tế trong knowledge base nội bộ. "
            "Dùng cho câu hỏi về triệu chứng, bệnh lý, thuốc, sức khỏe tâm thần."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Câu hỏi hoặc từ khóa cần tìm kiếm trong knowledge base",
                },
            },
            "required": ["query"],
        },
    },
}


def search_knowledge_base(
    query: str,
    collection_id: int,
    llm_service: LLMService,
    db: Session,
) -> tuple[str, list]:
    """Execute KB search. Returns (tool_result_str, sources_list)."""
    context, sources = llm_service.retrieve_context(query, db, collection_id)
    if not context:
        return "Không tìm thấy thông tin liên quan trong knowledge base.", []
    source_titles = ", ".join(s["title"] for s in sources) if sources else "N/A"
    return f"Knowledge base results (sources: {source_titles}):\n{context}", sources
