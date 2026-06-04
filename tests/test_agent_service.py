# tests/test_agent_service.py
import json
from unittest.mock import MagicMock
from app.services.agent_service import AgentService


def _make_llm_mock():
    mock = MagicMock()
    mock.retrieve_context.return_value = ("some context", [])
    return mock


def _make_completion(content=None, tool_calls=None):
    """Build a mock non-streaming completion response."""
    msg = MagicMock()
    msg.content = content
    msg.tool_calls = tool_calls
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _make_tool_call(call_id: str, name: str, args: dict):
    tc = MagicMock()
    tc.id = call_id
    tc.function.name = name
    tc.function.arguments = json.dumps(args)
    return tc


def _make_stream_chunk(text: str | None):
    delta = MagicMock()
    delta.content = text
    choice = MagicMock()
    choice.delta = delta
    chunk = MagicMock()
    chunk.choices = [choice]
    return chunk


# ── run() tests ──

def test_run_no_tools_returns_text():
    mock_llm = _make_llm_mock()
    mock_llm.client.chat.completions.create.return_value = _make_completion(
        content="VietCare can help you."
    )
    service = AgentService(mock_llm)
    result = service.run(query="hello", collection_id=1, db=MagicMock())

    assert result["text"] == "VietCare can help you."
    assert "sources" in result


def test_run_calls_kb_tool_and_retrieve_context_is_called():
    mock_llm = _make_llm_mock()
    tool_call = _make_tool_call("c1", "search_knowledge_base", {"query": "fever"})

    mock_llm.client.chat.completions.create.side_effect = [
        _make_completion(tool_calls=[tool_call]),
        _make_completion(content="Fever answer."),
    ]

    service = AgentService(mock_llm)
    result = service.run(query="I have fever", collection_id=1, db=MagicMock())

    assert result["text"] == "Fever answer."
    mock_llm.retrieve_context.assert_called_once()
    args = mock_llm.retrieve_context.call_args[0]
    assert args[0] == "fever"
    assert args[2] == 1


def test_run_returns_fallback_after_max_iterations():
    mock_llm = _make_llm_mock()
    tool_call = _make_tool_call("c1", "search_knowledge_base", {"query": "test"})
    mock_llm.client.chat.completions.create.return_value = _make_completion(tool_calls=[tool_call])

    service = AgentService(mock_llm)
    result = service.run(query="test", collection_id=1, db=MagicMock())

    assert "text" in result
    assert len(result["text"]) > 0
    assert mock_llm.client.chat.completions.create.call_count == AgentService.MAX_ITERATIONS


def test_run_unknown_tool_does_not_crash():
    mock_llm = _make_llm_mock()
    tool_call = _make_tool_call("c1", "nonexistent_tool", {})

    mock_llm.client.chat.completions.create.side_effect = [
        _make_completion(tool_calls=[tool_call]),
        _make_completion(content="Recovered."),
    ]

    service = AgentService(mock_llm)
    result = service.run(query="test", collection_id=1, db=MagicMock())

    assert result["text"] == "Recovered."


# ── stream() tests ──

def test_stream_yields_chunks_when_no_tools():
    mock_llm = _make_llm_mock()

    mock_llm.client.chat.completions.create.side_effect = [
        _make_completion(content=None, tool_calls=None),
        iter([_make_stream_chunk("Hello "), _make_stream_chunk("world")]),
    ]

    service = AgentService(mock_llm)
    chunks = list(service.stream(query="hello", collection_id=1, db=MagicMock()))

    assert "Hello " in chunks
    assert "world" in chunks


def test_stream_resolves_tool_then_streams():
    mock_llm = _make_llm_mock()
    tool_call = _make_tool_call("c1", "search_knowledge_base", {"query": "fever"})

    mock_llm.client.chat.completions.create.side_effect = [
        _make_completion(tool_calls=[tool_call]),
        _make_completion(content=None, tool_calls=None),
        iter([_make_stream_chunk("Fever answer "), _make_stream_chunk("streamed.")]),
    ]

    service = AgentService(mock_llm)
    chunks = list(service.stream(query="fever", collection_id=1, db=MagicMock()))

    assert "Fever answer " in chunks
    mock_llm.retrieve_context.assert_called_once()


def test_stream_yields_fallback_on_max_iterations():
    mock_llm = _make_llm_mock()
    tool_call = _make_tool_call("c1", "search_knowledge_base", {"query": "test"})
    mock_llm.client.chat.completions.create.return_value = _make_completion(tool_calls=[tool_call])

    service = AgentService(mock_llm)
    chunks = list(service.stream(query="test", collection_id=1, db=MagicMock()))

    assert len(chunks) == 1
    assert len(chunks[0]) > 0


def test_stream_skips_none_chunks():
    mock_llm = _make_llm_mock()
    mock_llm.client.chat.completions.create.side_effect = [
        _make_completion(content=None, tool_calls=None),
        iter([_make_stream_chunk("text"), _make_stream_chunk(None), _make_stream_chunk("more")]),
    ]

    service = AgentService(mock_llm)
    chunks = list(service.stream(query="hi", collection_id=1, db=MagicMock()))

    assert None not in chunks
    assert "text" in chunks
    assert "more" in chunks
