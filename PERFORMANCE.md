# Performance Notes

## Incident: Unbounded retrieval-retry loop on ambiguous hash-name queries

**Date found:** 2026-07-29 · **Status:** Fixed, validated · **Severity:** High (cost + latency, one instance hit an OpenAI rate limit)

### Summary

Ambiguous queries where the requested term doesn't literally appear in the
source document (e.g. asking for **"SHA2"** when the PDF only lists
`SHA-256`/`SHA-384`/`SHA-512`) could cause the agent to retry `search_child_chunks`
indefinitely — trying many phrasings of the same query — instead of stopping
and returning a "not found" answer. This was invisible in normal application
logs; it only became visible once [AgentOps](../agentops) instrumentation was
added and individual traces could be inspected.

### Impact (observed via AgentOps trace data)

| Trace ID | Query | Spans | Duration | Outcome |
|---|---|---|---|---|
| `af642cd2-05f1-4b11-927c-79ee25b1fe68` | "MD5 hash value" | 80+ | 29.3s | Eventually answered correctly (term *did* exist in doc) |
| `824c75c2-2260-493d-9d96-cd5537afae6c` | "hash value of SHA2?" | 80+ | 41.1s | Eventually answered correctly |
| `11425dbd-1cad-464f-bef4-1e99fa750752` | "MD5 hash value" | **106** (verified) | 47.7s | **Crashed**: OpenAI 429 — org hit its 200k TPM limit mid-request |

For comparison, unambiguous queries that matched document terms directly
resolved in 3–7 spans and 6–10 seconds (e.g. `9f128790-...`, "hash value of
md5?", 3 reasoning steps, 6.4s).

### Root cause

Two compounding issues, both surfaced by inspecting the failing trace and its
git history:

1. **No iteration cap.** The agent's `agent ↔ tools` LangGraph loop
   (`rag_agent/graph.py`) had no logic to stop retrying — it kept calling
   tools for as long as the LLM's tool-calling decision said to. On
   ambiguous terms, the LLM would try `SHA2`, `SHA-2`, `SHA-256`, `SHA-512`,
   `SHA2 hash`, `SHA-2 hash value`, etc., dozens of times.
2. **A dead config reference.** Commit `80e2d5e` ("fix recursion limit
   config") changed `cfg["recursion_limit"] = 50` (hardcoded) to
   `cfg["recursion_limit"] = config.RECURSION_LIMIT` — but `RECURSION_LIMIT`
   was never actually added to `config.py`. Even if it had been, LangGraph's
   default behavior on hitting a recursion limit is to raise
   `GraphRecursionError` — a crash, not a graceful stop.
3. **LLM stochasticity, not a deterministic bug.** The same exact query
   ("hash value for SHA2?") sometimes resolved in 3 tool calls and sometimes
   spiraled past 90 — with identical retrieval results at every step
   (`result_count: 2, top_score: 0.833` throughout). The model's willingness
   to accept a partial match varies run to run. This means the fix couldn't
   be "make the LLM smarter" — it needed to be a hard ceiling that bounds
   the worst case regardless of what the model decides.

### Fix

- **`config.py`**: added `MAX_AGENT_TOOL_CALLS = 6` (soft cap) and the
  previously-missing `RECURSION_LIMIT = 30` (hard backstop, well above the
  soft cap so it should never normally trigger).
- **`rag_agent/graph_state.py`**: added `tool_call_count` to `AgentState`.
- **`rag_agent/nodes.py`**: `agent_node` increments the counter each pass
  and stamps it onto the AgentOps span's attributes, so the count is visible
  in trace data going forward.
- **`rag_agent/edges.py`**: new `route_agent_or_stop()` wraps LangGraph's
  built-in `tools_condition` — once `tool_call_count >= MAX_AGENT_TOOL_CALLS`,
  it forces routing to `END` regardless of what the LLM wants, which lands
  on `extract_final_answer`'s existing graceful fallback
  ("Unable to generate an answer.") instead of looping further or crashing.

Semantics: with the cap at N, the agent gets at most N reasoning passes and
up to N−1 *completed* tool calls (the last pass's requested tool call is
discarded when the cap forces a stop before it executes).

### Validation

Two tests, both via real trace data:

1. **Forced trigger** (`MAX_AGENT_TOOL_CALLS` temporarily set to `1`): trace
   `e110db79-feb7-4d55-b71e-1e059db0be6b` — exactly 1 reasoning step, cap
   fired immediately, landed on the graceful fallback, `status: "ok"`,
   4.36s total. Confirmed the stop mechanism itself works before testing at
   production settings.
2. **Production settings** (`MAX_AGENT_TOOL_CALLS = 6`), same trigger
   phrase as the original incident ("hash value for SHA2?"): trace
   `18f4ee3e-d296-46b5-862a-981f307083d1` — exactly 6 reasoning steps
   (`tool_call_count` 1→6), 7.9s total, ~$0.0016, `status: "ok"`, graceful
   "couldn't find" answer. No crash.

**Before vs. after, same trigger phrase:**

| | Before | After |
|---|---|---|
| Spans | 80+ (106 in the crash case) | 7 |
| Duration | 40–48s | 7.9s |
| Outcome | Eventually correct, or crashed on rate limit | Graceful "not found" |
| Cost | Uncapped (contributed to hitting org TPM limit) | Bounded, ~$0.0016 |

### Known follow-ups (not yet done)

- `analyze_and_rewrite_query`'s LLM call (uses `with_structured_output`)
  doesn't expose token usage the same way `agent_reasoning_step` does, so
  its cost isn't currently tracked in AgentOps spans — a real gap in total
  cost accounting, separate fix needed.
- `MAX_AGENT_TOOL_CALLS = 6` is a reasonable starting value based on
  observing that legitimate multi-step answers needed at most 3 calls, but
  hasn't been tuned against a larger sample. Worth revisiting once more
  production trace data accumulates.
- The underlying "why does the agent sometimes accept a partial match and
  sometimes not" question is unresolved — the cap treats the symptom
  (unbounded cost/latency), not the cause (query-rewriting/retrieval
  confidence logic). A better long-term fix might involve a stricter
  early-stop condition based on retrieval score rather than a fixed call
  count.
