# AgentOps Instrumentation

This repo is instrumented with [AgentOps](../agentops) — every RAG query now
produces a real execution trace (spans for the agent's reasoning step,
retrieval calls, and the final synthesis LLM call), with cost and latency
attached to each.

## What changed

- **`core/observability.py`** (new) — a thin shim around `AgentOpsClient`.
  Exposes `trace(...)` and `span(...)` context managers. Uses a `contextvar`
  to track "the currently active trace" so any module in the call stack
  (`rag_agent/nodes.py`, `rag_agent/tools.py`) can attach a span without the
  orchestrator having to pass a client object through every function
  signature or through LangGraph's node/tool wiring.
- **`core/rag_orchestrator.py`** — `invoke()` and `stream()` each open one
  top-level trace per request (`trace_id` = the existing `request_id`, so
  AgentOps traces line up 1:1 with this app's own request IDs and log lines).
- **`rag_agent/nodes.py`** — spans added around every LLM call:
  `summarize_conversation`, `analyze_and_rewrite_query`,
  `agent_reasoning_step` (the tool-calling step), `aggregate_and_synthesize`
  (final answer generation). Token usage and estimated cost are attached
  where the LangChain response exposes `usage_metadata`.
- **`rag_agent/tools.py`** — spans added around `search_child_chunks`
  (kind=`retrieval`), `retrieve_parent_chunk(s)`. Captures result count and
  top similarity score.

## Why it's safe to merge

Instrumentation is designed to never be able to break the pipeline it's
watching:

- If `agentops-client` isn't installed, `core/observability.py` catches the
  `ImportError` and every `trace()`/`span()` call becomes a no-op.
- If the AgentOps server is unreachable, `AgentOpsClient` logs a warning and
  swallows the error rather than raising (see `agentops/client`).
- No existing function signatures changed in a way that affects callers —
  spans wrap the LLM/retrieval calls in place.

## Trace shape you'll see

```
rag_invoke_query (trace, trace_id = request_id)
└── agent_reasoning_step        [kind=agent]   ← the LLM decides whether to call tools
    └── search_child_chunks     [kind=retrieval]  ← nested: happens inside the agent's tool call
└── aggregate_and_synthesize    [kind=llm]     ← final answer generation
```

(`analyze_and_rewrite_query` and `summarize_conversation` also appear as
sibling spans on multi-turn conversations, before `agent_reasoning_step`.)

## Configuration

Point instrumentation at a different AgentOps server via:

```bash
export AGENTOPS_URL=http://127.0.0.1:8123   # default
```

## Running it

See the root `AgentOps` repo's `README.md` for full local setup. Short
version: start the AgentOps server, `pip install -e ../agentops/client`,
then run this app as normal — every query now produces a trace visible via
`GET http://127.0.0.1:8123/v1/traces?project=agentic-rag-orchestrator`.
