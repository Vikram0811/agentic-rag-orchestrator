"""
Structured response contracts for the RAG system.
The UI only ever sees these types — nothing from LangGraph, Qdrant, or LangChain.
"""
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ErrorType(str, Enum):
    RETRIEVAL_EMPTY   = "retrieval_empty"    # no chunks above threshold
    LLM_TIMEOUT       = "llm_timeout"        # asyncio.TimeoutError
    GRAPH_ERROR       = "graph_error"        # LangGraph recursion or state error
    OFF_TOPIC         = "off_topic"          # graph completed, no answer yielded
    UNEXPECTED        = "unexpected"         # catch-all


@dataclass
class SourceReference:
    filename: str
    score: float
    preview: str


@dataclass
class RAGResponse:
    answer: str
    sources: list[SourceReference]
    confidence: float
    latency_ms: int
    request_id: str
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None

    def to_display(self) -> str:
        """Render answer + collapsible sources for Gradio markdown."""
        if self.error:
            return f"❌ {self.error}"

        content = self.answer.strip()

        if self.sources:
            source_lines = "\n".join(
                f"- `{s.filename}` — score: {s.score:.2f}"
                for s in self.sources
            )
            content += f"\n\n<details><summary>📎 Sources ({len(self.sources)})</summary>\n\n{source_lines}\n\n</details>"

        return content


@dataclass
class StreamEvent:
    """Typed events yielded by the streaming path."""
    type: str          # "token" | "done" | "error" | "meta"
    content: str = ""
    meta: dict = field(default_factory=dict)