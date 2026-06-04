# tests/test_kb_tool.py
from unittest.mock import MagicMock
from app.services.tools.kb_tool import search_knowledge_base, KB_TOOL_SCHEMA


def test_schema_name():
    assert KB_TOOL_SCHEMA["function"]["name"] == "search_knowledge_base"


def test_schema_has_query_parameter():
    props = KB_TOOL_SCHEMA["function"]["parameters"]["properties"]
    assert "query" in props


def test_schema_query_is_required():
    required = KB_TOOL_SCHEMA["function"]["parameters"]["required"]
    assert "query" in required


def test_search_returns_formatted_string_and_sources():
    mock_llm = MagicMock()
    mock_llm.retrieve_context.return_value = (
        "Headache can be caused by stress.",
        [{"url": "faq://1", "title": "FAQ 1"}],
    )
    mock_db = MagicMock()

    result_str, sources = search_knowledge_base(query="headache", collection_id=1, llm_service=mock_llm, db=mock_db)

    mock_llm.retrieve_context.assert_called_once_with("headache", mock_db, 1)
    assert "Headache can be caused by stress." in result_str
    assert sources == [{"url": "faq://1", "title": "FAQ 1"}]


def test_search_empty_context_returns_tuple():
    mock_llm = MagicMock()
    mock_llm.retrieve_context.return_value = ("", [])
    mock_db = MagicMock()

    result_str, sources = search_knowledge_base(query="xyz", collection_id=1, llm_service=mock_llm, db=mock_db)

    assert isinstance(result_str, str)
    assert len(result_str) > 0
    assert sources == []
