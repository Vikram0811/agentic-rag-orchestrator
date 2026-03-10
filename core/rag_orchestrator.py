"""
RAGOrchestrator — owns all interaction with LangGraph.

Responsibilities:
- Build initial graph state from a raw query
- Run the graph (blocking path for tests/fallback)
- Stream graph events as typed StreamEvent objects (production path)
- Extract sources from graph state

The UI and ChatService never touch LangGraph types directly.
"""
import time
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage

from core.schemas import RAGResponse, SourceReference, StreamEvent
from core.logging_config import logger


class RAGOrchestrator:

    def __init__(self, container):
        """
        container: AppContainer — gives access to agent_graph, parent_store,
                   get_config(), reset_thread()
        """
        self._container = container

    # ------------------------------------------------------------------
    # Public: async streaming (production path)
    # ------------------------------------------------------------------

    # After the astream_events loop completes, do one final invoke to get state
    # OR track via a mutable closure during streaming:

    async def stream(self, query: str, request_id: str, session_id: str):
        initial_state = self._build_state(query, request_id)
        config = self._build_config(request_id, session_id)
        t0 = time.monotonic()
        retrieval_start = None
        generation_start = None
        retrieval_ms = 0
        generation_ms = 0
        partial = ""

        async for event in self._container.agent_graph.astream_events(
            initial_state, config, version="v2"
        ):
            kind = event.get("event")
            node = event.get("metadata", {}).get("langgraph_node", "")

            # Track retrieval timing via node entry/exit events
            if kind == "on_chain_start" and node == "process_question":
                retrieval_start = time.monotonic()
            elif kind == "on_chain_end" and node == "process_question":
                if retrieval_start:
                    retrieval_ms = int((time.monotonic() - retrieval_start) * 1000)

            if kind == "on_chain_start" and node == "aggregate":
                generation_start = time.monotonic()
            elif kind == "on_chain_end" and node == "aggregate":
                if generation_start:
                    generation_ms = int((time.monotonic() - generation_start) * 1000)

            if kind == "on_chat_model_stream" and node == "aggregate":
                chunk = event["data"]["chunk"].content
                if chunk:
                    partial += chunk
                    yield StreamEvent(type="token", content=partial)

        total_ms = int((time.monotonic() - t0) * 1000)
        logger.info(
            "stream_completed",
            extra={
                "request_id": request_id,
                "query": query,
                "retrieval_ms": retrieval_ms,
                "generation_ms": generation_ms,
                "total_ms": total_ms,
            }
        )
        yield StreamEvent(type="done", meta={"latency_ms": total_ms})

    # ------------------------------------------------------------------
    # Public: synchronous invoke (test / fallback path)
    # ------------------------------------------------------------------

    def invoke(self, query: str, request_id: str, session_id: str) -> RAGResponse:
        t0 = time.monotonic()
        initial_state = self._build_state(query, request_id)
        config = self._build_config(request_id, session_id)

        try:
            result = self._container.agent_graph.invoke(initial_state, config)
            answer = self._extract_answer(result)
            sources = self._extract_sources(result)
            confidence = self._compute_confidence(sources)
            latency_ms = int((time.monotonic() - t0) * 1000)

            logger.info(
                "invoke_completed",
                extra={
                    "request_id": request_id,
                    "query": query,
                    "retrieval_ms": result.get("retrieval_ms", 0),
                    "generation_ms": result.get("generation_ms", 0),
                    "total_ms": latency_ms,
                    "source_count": len(sources),
                    "confidence": confidence,
                    "error": None,
                }
            )

            return RAGResponse(
                answer=answer,
                sources=sources,
                confidence=confidence,
                latency_ms=latency_ms,
                request_id=request_id,
            )

        except Exception as e:
            latency_ms = int((time.monotonic() - t0) * 1000)
            logger.error(
                "invoke_failed",
                extra={"request_id": request_id, "error": str(e), "total_ms": latency_ms}
            )
            return RAGResponse(
                answer="",
                sources=[],
                confidence=0.0,
                latency_ms=latency_ms,
                request_id=request_id,
                error=str(e),
            )

    def reset_session(self, session_id: str):
        self._container.reset_thread(session_id)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_state(self, query: str, request_id: str) -> dict:
        all_files = self._container.parent_store.load_content_many(
            [
                pid.stem
                for pid in self._container.parent_store
                    ._ParentStoreManager__store_path.glob("*.json")
            ]
        )
        unique_filenames = set(
            doc["metadata"].get("source", "Unknown") for doc in all_files
        )
        return {
            "messages": [HumanMessage(content=query.strip())],
            "document_count": len(unique_filenames),
            "document_names": list(unique_filenames),
            "trace_id": request_id,
        }

    def _build_config(self, request_id: str, session_id: str) -> dict:
        cfg = self._container.get_config(session_id)
        cfg.setdefault("configurable", {})
        cfg["configurable"]["trace_id"] = request_id
        cfg["recursion_limit"] = 50
        return cfg

    def _extract_answer(self, result: dict) -> str:
        messages = result.get("messages", [])
        for msg in reversed(messages):
            if isinstance(msg, AIMessage) and msg.content and not getattr(msg, "tool_calls", None):
                return msg.content.strip()
        return "I couldn't find relevant information for your query."

    def _extract_sources(self, result: dict) -> list[SourceReference]:
        """
        Pulls source metadata surfaced by aggregate_responses node.
        Extend this when you thread retrieved_sources through graph state.
        """
        doc_names = result.get("document_names", [])
        return [
            SourceReference(filename=Path(f).name, score=0.0, preview="")
            for f in doc_names
        ]

    def _compute_confidence(self, sources: list[SourceReference]) -> float:
        if not sources:
            return 0.0
        scored = [s for s in sources if s.score > 0]
        if not scored:
            return 0.5   # sources found, scores not yet wired
        return round(sum(s.score for s in scored) / len(scored), 3)