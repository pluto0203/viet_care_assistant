# app/services/agent_service.py
"""
AgentService — Tool-calling Agent loop using OpenRouter function calling.
Replaces direct LLMService calls in ChatService for both sync and streaming responses.
"""
import json
from sqlalchemy.orm import Session

from app.config import config
from app.services.llm import LLMService
from app.services.tools.kb_tool import KB_TOOL_SCHEMA, search_knowledge_base
from app.services.tools.hospital_tool import HOSPITAL_TOOL_SCHEMA, find_nearby_hospitals
from app.core.exceptions import LLMServiceError
from app.core.logging import get_logger

logger = get_logger(__name__)

AGENT_SYSTEM_PROMPT = (
    "You are VietCare Assistant — a professional, empathetic healthcare AI. "
    "You have tools available: search the medical knowledge base and find nearby hospitals. "
    "Use tools when they help give a more accurate, grounded answer. "
    "Always recommend consulting a doctor for serious symptoms. "
    "Respond in the same language as the user's question."
)

TOOLS = [KB_TOOL_SCHEMA, HOSPITAL_TOOL_SCHEMA]


class AgentService:
    MAX_ITERATIONS = 5

    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
        self.client = llm_service.client

    # ── Message Building ──

    def _build_messages(self, history: list | None, query: str) -> list[dict]:
        messages = [{"role": "system", "content": AGENT_SYSTEM_PROMPT}]
        if history:
            for msg in history[-config.MAX_HISTORY_MESSAGES:]:
                messages.append({"role": msg.role, "content": msg.content})
        messages.append({"role": "user", "content": query})
        return messages

    # ── Tool Execution ──

    def _execute_tool(self, tool_call, collection_id: int, db: Session) -> tuple[str, list]:
        """Execute a tool call. Returns (result_str, sources_list)."""
        name = tool_call.function.name
        try:
            args = json.loads(tool_call.function.arguments)
        except json.JSONDecodeError:
            return f"Error: invalid tool arguments for {name}", []

        logger.info("tool_call", tool=name, args=args)

        if name == "search_knowledge_base":
            return search_knowledge_base(
                query=args.get("query", ""),
                collection_id=collection_id,
                llm_service=self.llm,
                db=db,
            )
        elif name == "find_nearby_hospitals":
            return find_nearby_hospitals(
                location=args.get("location", ""),
                radius_km=args.get("radius_km", 2),
                limit=args.get("limit", 5),
            ), []
        else:
            logger.warning("unknown_tool", tool=name)
            return f"Tool '{name}' is not available.", []

    # ── Non-streaming Run ──

    def run(
        self,
        query: str,
        collection_id: int,
        db: Session,
        history: list | None = None,
    ) -> dict:
        """
        Run the agent loop until final answer or MAX_ITERATIONS.
        Returns: {"text": "...", "sources": [...]}
        Raises: LLMServiceError on LLM failure or max iterations reached.
        """
        messages = self._build_messages(history, query)
        accumulated_sources: list = []

        for iteration in range(self.MAX_ITERATIONS):
            try:
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS,
                )
            except Exception as e:
                logger.error("agent_llm_error", error=str(e), iteration=iteration)
                raise LLMServiceError(f"LLM call failed: {e}")

            msg = response.choices[0].message

            if not msg.tool_calls:
                logger.info("agent_done", iterations=iteration + 1)
                return {"text": msg.content or "", "sources": accumulated_sources}

            messages.append(msg)
            for tool_call in msg.tool_calls:
                result, sources = self._execute_tool(tool_call, collection_id, db)
                accumulated_sources.extend(sources)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        logger.warning("agent_max_iterations_reached", query=query)
        raise LLMServiceError("Agent reached maximum iterations without generating a final answer")

    # ── Streaming ──

    def stream(
        self,
        query: str,
        collection_id: int,
        db: Session,
        history: list | None = None,
    ):
        """
        Stream the agent response.
        Phase 1: Resolve tool calls (non-streaming) until no more tool calls.
        - If no tools needed: yield Phase 1 answer directly (no extra LLM call).
        - If tools used: proceed to Phase 2.
        Phase 2: Stream final answer with accumulated tool context.
        Raises: LLMServiceError on failure or max iterations (never yields error strings).
        """
        messages = self._build_messages(history, query)
        tools_were_called = False

        # Phase 1: Resolve tool calls
        for iteration in range(self.MAX_ITERATIONS):
            try:
                response = self.client.chat.completions.create(
                    model=config.LLM_MODEL,
                    messages=messages,
                    tools=TOOLS,
                    tool_choice="auto",
                    temperature=config.LLM_TEMPERATURE,
                    max_tokens=config.LLM_MAX_TOKENS,
                )
            except Exception as e:
                logger.error("agent_stream_phase1_error", error=str(e))
                raise LLMServiceError(f"LLM call failed: {e}")

            msg = response.choices[0].message

            if not msg.tool_calls:
                if not tools_were_called:
                    # No tools needed — yield Phase 1 answer directly, skip Phase 2
                    if msg.content:
                        yield msg.content
                    return
                # Tools were used, got final answer — proceed to Phase 2 for streaming
                break

            tools_were_called = True
            messages.append(msg)
            for tool_call in msg.tool_calls:
                result, _ = self._execute_tool(tool_call, collection_id, db)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            # Loop exhausted without break — max iterations reached
            logger.warning("agent_stream_max_iterations", query=query)
            raise LLMServiceError("Agent reached maximum iterations without generating a final answer")

        # Phase 2: Stream final answer with tool context (only reached when tools were used)
        try:
            stream_response = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=messages,
                temperature=config.LLM_TEMPERATURE,
                max_tokens=config.LLM_MAX_TOKENS,
                stream=True,
            )
            for chunk in stream_response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error("agent_stream_phase2_error", error=str(e))
            raise LLMServiceError(f"LLM streaming failed: {e}")
