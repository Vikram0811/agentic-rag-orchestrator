"""
AgentOps instrumentation shim for agentic-rag-orchestrator.

Why this exists (rather than passing an AgentOpsClient / trace object through
every function call): the LangGraph node functions in rag_agent/nodes.py and
the tool functions in rag_agent/tools.py are invoked by LangGraph's runtime,
not called directly by RAGOrchestrator — there's no natural place to thread
a "current trace" argument through that call chain without changing every
node/tool signature and the graph wiring in rag_agent/graph.py.

Instead, RAGOrchestrator opens one trace per request via `trace(...)`, which
stores the active TraceHandle in a contextvar. Anywhere else in the call
stack — a node function, a tool function — can then call `span(...)` and it
attaches to whatever trace is currently active, with correct parent/child
nesting handled by AgentOpsClient's own thread-local span stack. This is the
same pattern real OpenTelemetry SDKs use (`tracer.start_as_current_span`),
which is intentional: swapping this shim's internals for real OTel later
should not require touching call sites in nodes.py/tools.py at all.

Fails safe by design: if agentops-client isn't installed, or the AgentOps
server is unreachable, every function here becomes a no-op. Instrumentation
must never be able to break the RAG pipeline it's observing.
"""

import contextlib
import contextvars
import logging
import os

logger = logging.getLogger("agentops.rag_orchestrator")

_current_trace = contextvars.ContextVar("agentops_current_trace", default=None)

try:
    from agentops_client import AgentOpsClient

    _client = AgentOpsClient(
        project="agentic-rag-orchestrator",
        base_url=os.environ.get("AGENTOPS_URL", "http://127.0.0.1:8123"),
    )
    ENABLED = True
except Exception as e:  # agentops-client not installed, or failed to init
    _client = None
    ENABLED = False
    logger.warning("AgentOps instrumentation disabled (agentops-client not available): %s", e)


# gpt-4o-mini pricing as of this writing, USD per token. Update if config.LLM_MODEL changes.
_PRICE_PER_TOKEN = {
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.60 / 1_000_000},
    "gpt-4o": {"input": 2.50 / 1_000_000, "output": 10.00 / 1_000_000},
}


def _normalize_model_name(model: str | None) -> str | None:
    """
    OpenAI's API returns dated model IDs in response_metadata (e.g.
    'gpt-4o-mini-2024-07-18'), not the stable alias used in config.py
    ('gpt-4o-mini'). Pricing is keyed by the alias, so match by prefix —
    this also means pricing keeps working automatically if OpenAI bumps
    the dated snapshot without us needing to update this table.
    """
    if not model:
        return model
    for known in _PRICE_PER_TOKEN:
        if model == known or model.startswith(known + "-"):
            return known
    return model


def estimate_cost_usd(model: str, input_tokens: int, output_tokens: int) -> float | None:
    prices = _PRICE_PER_TOKEN.get(_normalize_model_name(model))
    if not prices or input_tokens is None or output_tokens is None:
        return None
    return round(input_tokens * prices["input"] + output_tokens * prices["output"], 8)


def usage_from_ai_message(msg) -> dict:
    """
    Best-effort extraction of token usage from a LangChain AIMessage.
    Different providers/langchain versions surface this differently, so we
    check the common spots and degrade to Nones rather than raising —
    an instrumentation helper must never crash the pipeline it's watching.
    """
    usage = getattr(msg, "usage_metadata", None)
    if usage:
        return {
            "input_tokens": usage.get("input_tokens"),
            "output_tokens": usage.get("output_tokens"),
        }
    meta = getattr(msg, "response_metadata", None) or {}
    token_usage = meta.get("token_usage") or {}
    return {
        "input_tokens": token_usage.get("prompt_tokens"),
        "output_tokens": token_usage.get("completion_tokens"),
    }


class _NullSpan:
    """No-op span returned when instrumentation is disabled or no trace is active."""

    def set_output(self, *_a, **_k):
        pass

    def set_attribute(self, *_a, **_k):
        pass

    def set_llm_usage(self, *_a, **_k):
        pass


@contextlib.contextmanager
def trace(name: str, metadata: dict | None = None, trace_id: str | None = None):
    """Open a top-level AgentOps trace for one end-to-end request."""
    if not ENABLED:
        yield None
        return
    with _client.trace(name, metadata=metadata, trace_id=trace_id) as t:
        token = _current_trace.set(t)
        try:
            yield t
        finally:
            _current_trace.reset(token)


@contextlib.contextmanager
def span(name: str, kind: str = "chain", input_payload=None):
    """
    Attach a span to whatever trace is currently active (set by an
    enclosing `trace(...)` block higher up the call stack). Safe to call
    even when no trace is active or instrumentation is disabled — returns
    a no-op span in that case.
    """
    t = _current_trace.get()
    if not ENABLED or t is None:
        yield _NullSpan()
        return
    with t.span(name, kind=kind, input_payload=input_payload) as s:
        yield s