"""
ChatService — the single entry point the UI calls.

Responsibilities:
- Accept plain strings from the UI
- Enforce timeout
- Delegate to RAGOrchestrator
- Return structured RAGResponse or yield strings for streaming
- Log per-request structured metrics

The UI never sees LangGraph, Qdrant, or LangChain types.
"""
import asyncio
import uuid
from typing import AsyncGenerator

from core.response_cache import ResponseCache
from core.rag_orchestrator import RAGOrchestrator
from core.schemas import RAGResponse, ErrorType
from core.logging_config import logger

STREAM_TIMEOUT_SECONDS = 90


class ChatService:

    def __init__(self, orchestrator: RAGOrchestrator, cache: ResponseCache):
        self._orchestrator = orchestrator
        self._cache = cache

    # ------------------------------------------------------------------
    # Streaming path (Gradio async generator)
    # ------------------------------------------------------------------

    async def stream_ask(self, query: str, session_id: str) -> AsyncGenerator[str, None]:
        """
        Yields progressive answer strings for Gradio ChatInterface.
        Handles timeout and errors — never raises to the UI.
        """
        request_id = str(uuid.uuid4())

        # Cache check — return immediately if hit
        hit = self._cache.get(session_id, query)
        if hit:
            answer, scope = hit
            logger.info(
                "cache_hit",
                extra={"request_id": request_id, "query": query, "scope": scope}
            )
            yield answer
            return
        
        partial = ""
        yielded = False

        try:
            async with asyncio.timeout(STREAM_TIMEOUT_SECONDS):
                async for event in self._orchestrator.stream(query, request_id, session_id):
                    if event.type == "token":
                        partial = event.content
                        yielded = True
                        yield partial
                    elif event.type == "error":
                        yielded = True
                        yield f"❌ {event.content}"
                        return

        except asyncio.TimeoutError:
            logger.warning(
                "stream_error",
                extra={
                    "request_id": request_id,
                    "query": query,
                    "error_type": ErrorType.LLM_TIMEOUT,
                }
            )
            yielded = True
            if partial:
                yield partial + "\n\n⚠️ Response timed out before completion."
            else:
                yield "⚠️ Request timed out. Please try again."

        except Exception as e:
            error_str = str(e)
            error_type = (
                ErrorType.GRAPH_ERROR
                if "recursion" in error_str.lower() or "langgraph" in error_str.lower()
                else ErrorType.UNEXPECTED
            )
            logger.error(
                "stream_error",
                extra={
                    "request_id": request_id,
                    "query": query,
                    "error_type": error_type,
                    "error": error_str,
                }
            )
            yielded = True
            yield f"❌ Unexpected error: {error_str}"
            return
        
        # Always runs after the async for loop completes normally
        if not yielded:
            logger.info(
                "stream_error",
                extra={
                    "request_id": request_id,
                    "query": query,
                    "error_type": ErrorType.OFF_TOPIC,
                }
            )
            yield "I can only answer questions about the uploaded documents."
            return

        # Store successful answer in cache
        if partial:
            self._cache.set(session_id, query, partial)

    # ------------------------------------------------------------------
    # Blocking path (tests, batch, fallback)
    # ------------------------------------------------------------------

    def ask(self, query: str, session_id: str) -> RAGResponse:
        """Synchronous ask — returns a fully structured RAGResponse."""
        request_id = str(uuid.uuid4())
        return self._orchestrator.invoke(query, request_id, session_id)

    # ------------------------------------------------------------------
    # Session control
    # ------------------------------------------------------------------

    def reset_session(self, session_id: str):
        self._cache.clear_session(session_id)
        self._orchestrator.reset_session(session_id)