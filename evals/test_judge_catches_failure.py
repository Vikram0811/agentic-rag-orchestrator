"""
eval/test_judge_catches_failure.py — sanity check for the judge itself.

13/13 PASS is a good sign, but it doesn't prove the judge actually compares
values rather than defaulting to PASS regardless of input. This feeds it a
known-correct real answer against a *deliberately wrong* ground truth and
confirms it correctly returns FAIL — the judge equivalent of the loop-cap
forced-trigger test from earlier weeks.

Usage:
  python eval/test_judge_catches_failure.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
import config
from run_judge import judge_answer

sys.path.insert(0, str(Path(__file__).parent))


def main():
    judge_llm = ChatOpenAI(model=config.LLM_MODEL, temperature=0)

    # The REAL, correct MD5 answer (confirmed via multiple real traces
    # throughout this project) — but paired with a deliberately WRONG
    # ground truth, to see if the judge notices the mismatch.
    real_correct_answer = "The MD5 hash value is 807d8350a068ff6bedb50b131c9b6713."
    deliberately_wrong_ground_truth = "0000000000000000000000000000000"

    print("Testing: does the judge catch a mismatch?")
    print(f"  Agent's actual answer:  {real_correct_answer}")
    print(f"  Ground truth given:     {deliberately_wrong_ground_truth}  (deliberately wrong)")
    print()

    verdict = judge_answer(
        judge_llm,
        question="What is the MD5 hash value?",
        ground_truth=deliberately_wrong_ground_truth,
        expect_found=True,
        actual_answer=real_correct_answer,
    )

    print(f"Verdict: {'PASS' if verdict.passed else 'FAIL'}  (score={verdict.score})")
    print(f"Rationale: {verdict.rationale}")
    print()

    if verdict.passed:
        print("❌ SANITY CHECK FAILED: judge said PASS despite a real mismatch.")
        print("   This means the judge may not be comparing values correctly —")
        print("   worth investigating before trusting any of its verdicts.")
        sys.exit(1)
    else:
        print("✓ SANITY CHECK PASSED: judge correctly caught the mismatch.")
        print("  This confirms the 13/13 result from the real run is a genuine")
        print("  signal, not the judge defaulting to PASS regardless of input.")


if __name__ == "__main__":
    main()