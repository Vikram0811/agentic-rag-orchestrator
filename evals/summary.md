# RAG Evaluation Summary

**Date:** 2026-06-09 09:51
**Dataset:** 15 questions
**Model:** gpt-4o-mini
**Retrieval Threshold:** 0.62
**Evaluation Method:** Direct retrieval + generation (bypasses LangGraph agent)

## Scores

| Metric | Score | Threshold | Status |
|---|---|---|---|
| Faithfulness | 0.333 | > 0.8 | ❌ Needs attention |
| Answer Relevancy | 0.324 | > 0.8 | ❌ Needs attention |
| Context Recall | 0.6 | > 0.7 | ⚠️ Acceptable |

## What Each Metric Means

- **Faithfulness** — are answers grounded in retrieved context, not hallucinated?
- **Answer Relevancy** — do answers actually address what was asked?
- **Context Recall** — does retrieval find the chunks needed to answer correctly?

## Configuration

| Parameter | Value |
|---|---|
| RAG_MIN_RETRIEVAL_SCORE | 0.62 |
| CHILD_CHUNK_SIZE | 500 |
| CHILD_CHUNK_OVERLAP | 100 |
| MIN_PARENT_SIZE | 2000 |
| MAX_PARENT_SIZE | 10000 |
| TOP_K_CHUNKS | 5 |
