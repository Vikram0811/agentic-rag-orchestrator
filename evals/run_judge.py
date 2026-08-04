"""
eval/run_judge.py — AgentOps trace-based LLM-as-a-Judge harness.

Unlike evals/run_evals.py (which bypasses the agent entirely and evaluates
retrieval+generation directly with Ragas), this script exercises the real
production path: it calls RAGOrchestrator.invoke() exactly as app.py does,
which means every run here produces a real AgentOps trace via the
instrumentation already built in Weeks 1-2 — no new tracing code needed.

Per question:
  1. Call orchestrator.invoke(question) — a real agent run, real trace emitted
  2. Fetch that trace back from AgentOps (GET /v1/traces/{trace_id})
  3. Ask a judge LLM: does the agent's actual answer match the ground truth?
  4. Write the verdict to AgentOps (POST /v1/evals) — trace_id ties it back
     to the exact run that produced it, so it's always auditable against
     the real spans (tokens, cost, tool calls) that led to that answer.

Usage:
  python eval/run_judge.py
"""

import json
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import httpx
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from core.app_container import AppContainer
from core.rag_orchestrator import RAGOrchestrator
import config


DATASET_PATH = Path(__file__).parent / "judge_dataset.json"
AGENTOPS_URL = "http://127.0.0.1:8123"
JUDGE_VERSION = "v1"
CHECK_NAME = "golden_answer_match"


class JudgeVerdict(BaseModel):
    passed: bool = Field(description="True if the answer correctly matches the ground truth")
    score: float = Field(description="0.0 to 1.0 confidence in the verdict")
    rationale: str = Field(description="One or two sentences explaining the verdict")


JUDGE_SYSTEM_PROMPT = """You are grading whether an AI agent's answer is correct.

You will be given:
- A question
- The ground truth answer
- Whether the ground truth is expected to exist in the source document
  (expect_found)
- The agent's actual answer

Grading rules:
- If expect_found is true: PASS only if the agent's answer contains the
  exact ground truth value. A close-but-wrong value (e.g. a truncated or
  garbled hash) is a FAIL, not a partial pass — exactness matters for
  values like hashes.
- If expect_found is false: PASS if the agent correctly indicates the
  information could not be found, rather than fabricating a plausible-
  looking but incorrect answer. FAIL if the agent hallucinates a value.
- Ignore formatting differences (markdown, capitalization, surrounding
  prose) — judge the substance of the answer only.
"""


def load_dataset() -> list[dict]:
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def judge_answer(judge_llm, question: str, ground_truth: str, expect_found: bool, actual_answer: str) -> JudgeVerdict:
    structured_judge = judge_llm.with_structured_output(JudgeVerdict)
    user_prompt = (
        f"Question: {question}\n"
        f"Ground truth: {ground_truth}\n"
        f"Expected to be found in source document: {expect_found}\n"
        f"Agent's actual answer: {actual_answer}"
    )
    return structured_judge.invoke([
        SystemMessage(content=JUDGE_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt),
    ])


def post_eval_result(http_client: httpx.Client, trace_id: str, verdict: JudgeVerdict) -> None:
    try:
        resp = http_client.post("/v1/evals", json={
            "trace_id": trace_id,
            "check_name": CHECK_NAME,
            "check_type": "llm_judge",
            "judge_version": JUDGE_VERSION,
            "passed": verdict.passed,
            "score": verdict.score,
            "rationale": verdict.rationale,
        })
        resp.raise_for_status()
    except Exception as e:
        # An eval-writing failure shouldn't stop the rest of the run —
        # print it and keep going, same "never break the thing you're
        # observing" principle as the instrumentation itself.
        print(f"    ⚠ Failed to write eval result to AgentOps: {e}")


def main():
    print("=" * 60)
    print("AgentOps Trace-Based Judge")
    print("=" * 60)

    print("Starting container...")
    container = AppContainer()
    container.start()
    orchestrator = RAGOrchestrator(container)
    print("Ready.\n")

    judge_llm = ChatOpenAI(model=config.LLM_MODEL, temperature=0)
    http_client = httpx.Client(base_url=AGENTOPS_URL, timeout=10.0)

    dataset = load_dataset()
    print(f"Loaded {len(dataset)} test cases.\n")

    results = []

    for i, item in enumerate(dataset, start=1):
        question = item["question"]
        print(f"[{i}/{len(dataset)}] {question}")

        request_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        response = orchestrator.invoke(question, request_id=request_id, session_id=session_id)

        if response.error:
            print(f"    ✗ Agent error: {response.error}")
            verdict = JudgeVerdict(passed=False, score=0.0, rationale=f"Agent errored: {response.error}")
        else:
            verdict = judge_answer(
                judge_llm,
                question=question,
                ground_truth=item["ground_truth"],
                expect_found=item["expect_found"],
                actual_answer=response.answer,
            )

        mark = "✓ PASS" if verdict.passed else "✗ FAIL"
        print(f"    {mark}  (score={verdict.score})  {verdict.rationale}")

        post_eval_result(http_client, trace_id=response.request_id, verdict=verdict)

        results.append({
            "id": item["id"],
            "question": question,
            "passed": verdict.passed,
            "score": verdict.score,
            "rationale": verdict.rationale,
            "trace_id": response.request_id,
        })

    # ── Summary ──────────────────────────────────────────────────────
    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed_count}/{total} passed")
    print("=" * 60)

    failed = [r for r in results if not r["passed"]]
    if failed:
        print("\nFailed cases:")
        for r in failed:
            print(f"  ✗ [{r['id']}] {r['question']}")
            print(f"      trace_id: {r['trace_id']}")
            print(f"      reason: {r['rationale']}")
    else:
        print("\nAll cases passed.")


if __name__ == "__main__":
    main()