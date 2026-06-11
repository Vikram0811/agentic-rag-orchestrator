"""
run_evals.py — RAG evaluation harness using Ragas.

Bypasses LangGraph entirely. Evaluates retrieval and generation
components directly — the correct industry approach for RAG evals.

Pipeline per question:
  1. Embed question → search Qdrant directly
  2. Retrieve parent chunks for full context
  3. Call GPT-4o-mini directly with retrieved context
  4. Feed question + answer + contexts + ground_truth to Ragas

Metrics:
  - Faithfulness:      Is the answer grounded in retrieved context?
  - Answer Relevancy:  Does the answer address the question asked?
  - Context Recall:    Did retrieval find the chunks needed to answer?

Usage:
  python evals/run_evals.py
"""

import json
import csv
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_recall
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import SystemMessage, HumanMessage
from datasets import Dataset

from db.vector_db_manager import VectorDbManager
from db.parent_store_manager import ParentStoreManager
import config


# ── Configuration ─────────────────────────────────────────────────
DATASET_PATH = Path(__file__).parent / "dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.csv"
SUMMARY_PATH = Path(__file__).parent / "summary.md"

RAG_SYSTEM_PROMPT = """You are a helpful assistant that answers questions strictly
based on the provided context. If the answer is not in the context, say
'I could not find this information in the provided documents.'
Do not use any external knowledge."""

TOP_K_CHUNKS = 5


# ── Setup ──────────────────────────────────────────────────────────
def setup_infrastructure():
    """Boot only what we need — vector DB and parent store. No LangGraph."""
    print("Booting infrastructure...")

    vector_db    = VectorDbManager()
    parent_store = ParentStoreManager()

    collection = vector_db.get_collection(config.CHILD_COLLECTION)
    llm        = ChatOpenAI(
        model=config.LLM_MODEL,
        temperature=0,
        api_key=config.OPENAI_API_KEY,
    )

    print("Infrastructure ready.\n")
    return collection, parent_store, llm


def load_dataset():
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    print(f"Loaded {len(data)} test cases.\n")
    return data


# ── Core RAG Pipeline (no LangGraph) ──────────────────────────────
def retrieve_chunks(collection, question: str) -> tuple[list[str], list[str]]:
    """
    Step 1 — Retrieve top-K child chunks from Qdrant directly.
    Returns (child_texts, parent_ids).
    """
    results = collection.similarity_search(question, k=TOP_K_CHUNKS)
    child_texts = [doc.page_content for doc in results if doc.page_content.strip()]
    parent_ids  = [
        doc.metadata.get("parent_id", "")
        for doc in results
        if doc.page_content.strip()
    ]
    return child_texts, parent_ids


def retrieve_parents(parent_store: ParentStoreManager, parent_ids: list[str]) -> list[str]:
    """
    Step 2 — Fetch parent chunks for full context.
    Falls back to child chunks if parent store is unavailable.
    """
    parent_texts = []
    seen = set()

    for pid in parent_ids:
        if pid and pid not in seen:
            try:
                parent = parent_store.get(pid)
                if parent and hasattr(parent, "page_content"):
                    parent_texts.append(parent.page_content)
                    seen.add(pid)
            except Exception:
                pass

    return parent_texts


def generate_answer(llm, question: str, contexts: list[str]) -> str:
    """
    Step 3 — Generate answer directly via LLM with retrieved context.
    No LangGraph, no agents, no tools.
    """
    if not contexts:
        return "I could not find this information in the provided documents."

    context_text = "\n\n---\n\n".join(contexts[:3])  # top 3 contexts

    messages = [
        SystemMessage(content=RAG_SYSTEM_PROMPT),
        HumanMessage(content=f"Context:\n{context_text}\n\nQuestion: {question}")
    ]

    try:
        response = llm.invoke(messages)
        return response.content.strip()
    except Exception as e:
        return f"Generation error: {str(e)}"


# ── Run All Questions ──────────────────────────────────────────────
def run_all_queries(collection, parent_store, llm, dataset: list) -> list[dict]:
    """Run all questions through the direct RAG pipeline."""
    results = []
    total   = len(dataset)

    for i, item in enumerate(dataset):
        question     = item["question"]
        ground_truth = item["ground_truth"]

        print(f"  [{i+1}/{total}] {question[:70]}...")

        try:
            # Step 1 — retrieve child chunks
            child_texts, parent_ids = retrieve_chunks(collection, question)

            # Step 2 — fetch parent chunks for full context
            parent_texts = retrieve_parents(parent_store, parent_ids)

            # Use parent texts if available, otherwise fall back to child texts
            contexts = parent_texts if parent_texts else child_texts

            # Step 3 — generate answer
            answer = generate_answer(llm, question, contexts)

            results.append({
                "question":     question,
                "answer":       answer,
                "contexts":     contexts if contexts else ["No context retrieved."],
                "ground_truth": ground_truth,
            })

            print(f"         ✓ {answer[:80]}...")

        except Exception as e:
            print(f"         ✗ Error: {e}")
            results.append({
                "question":     question,
                "answer":       f"Error: {str(e)}",
                "contexts":     ["No context retrieved."],
                "ground_truth": ground_truth,
            })

    return results


# ── Ragas Evaluation ───────────────────────────────────────────────
def run_ragas_evaluation(results: list[dict]) -> object:
    """Run Ragas metrics on collected results."""
    print("\nRunning Ragas evaluation...")

    dataset_dict = {
        "question":     [r["question"]     for r in results],
        "answer":       [r["answer"]       for r in results],
        "contexts":     [r["contexts"]     for r in results],
        "ground_truth": [r["ground_truth"] for r in results],
    }

    hf_dataset = Dataset.from_dict(dataset_dict)

    llm        = ChatOpenAI(model=config.LLM_MODEL, temperature=0)
    embeddings = OpenAIEmbeddings()

    ragas_llm        = LangchainLLMWrapper(llm)
    ragas_embeddings = LangchainEmbeddingsWrapper(embeddings)

    scores = evaluate(
        dataset=hf_dataset,
        metrics=[faithfulness, answer_relevancy, context_recall],
        llm=ragas_llm,
        embeddings=ragas_embeddings,
    )

    return scores


# ── Save Results ───────────────────────────────────────────────────
def save_results(results: list[dict], scores) -> tuple:
    scores_df = scores.to_pandas()

    # CSV
    with open(RESULTS_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "question", "answer", "ground_truth",
            "faithfulness", "answer_relevancy", "context_recall"
        ])
        writer.writeheader()
        for i, row in scores_df.iterrows():
            writer.writerow({
                "question":         results[i]["question"],
                "answer":           results[i]["answer"],
                "ground_truth":     results[i]["ground_truth"],
                "faithfulness":     round(row.get("faithfulness", 0), 3),
                "answer_relevancy": round(row.get("answer_relevancy", 0), 3),
                "context_recall":   round(row.get("context_recall", 0), 3),
            })

    print(f"\nDetailed results saved to: {RESULTS_PATH}")

    avg_f  = round(scores_df["faithfulness"].mean(), 3)
    avg_ar = round(scores_df["answer_relevancy"].mean(), 3)
    avg_cr = round(scores_df["context_recall"].mean(), 3)

    summary = f"""# RAG Evaluation Summary

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
**Dataset:** {len(results)} questions
**Model:** {config.LLM_MODEL}
**Retrieval Threshold:** {config.RAG_MIN_RETRIEVAL_SCORE}
**Evaluation Method:** Direct retrieval + generation (bypasses LangGraph agent)

## Scores

| Metric | Score | Threshold | Status |
|---|---|---|---|
| Faithfulness | {avg_f} | > 0.8 | {"✅ Strong" if avg_f > 0.8 else "⚠️ Acceptable" if avg_f > 0.6 else "❌ Needs attention"} |
| Answer Relevancy | {avg_ar} | > 0.8 | {"✅ Strong" if avg_ar > 0.8 else "⚠️ Acceptable" if avg_ar > 0.6 else "❌ Needs attention"} |
| Context Recall | {avg_cr} | > 0.7 | {"✅ Strong" if avg_cr > 0.7 else "⚠️ Acceptable" if avg_cr > 0.5 else "❌ Needs attention"} |

## What Each Metric Means

- **Faithfulness** — are answers grounded in retrieved context, not hallucinated?
- **Answer Relevancy** — do answers actually address what was asked?
- **Context Recall** — does retrieval find the chunks needed to answer correctly?

## Configuration

| Parameter | Value |
|---|---|
| RAG_MIN_RETRIEVAL_SCORE | {config.RAG_MIN_RETRIEVAL_SCORE} |
| CHILD_CHUNK_SIZE | {config.CHILD_CHUNK_SIZE} |
| CHILD_CHUNK_OVERLAP | {config.CHILD_CHUNK_OVERLAP} |
| MIN_PARENT_SIZE | {config.MIN_PARENT_SIZE} |
| MAX_PARENT_SIZE | {config.MAX_PARENT_SIZE} |
| TOP_K_CHUNKS | {TOP_K_CHUNKS} |
"""

    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Summary saved to: {SUMMARY_PATH}")
    return avg_f, avg_ar, avg_cr


# ── Main ───────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("RAG Evaluation Harness")
    print("=" * 60)

    # Boot infrastructure — no LangGraph
    collection, parent_store, llm = setup_infrastructure()

    # Load test dataset
    dataset = load_dataset()

    # Run all questions through direct RAG pipeline
    print("Running queries through direct RAG pipeline...")
    results = run_all_queries(collection, parent_store, llm, dataset)

    # Ragas evaluation
    scores = run_ragas_evaluation(results)

    # Save and print
    f, ar, cr = save_results(results, scores)

    print("\n" + "=" * 60)
    print("EVALUATION COMPLETE")
    print("=" * 60)
    print(f"  Faithfulness:      {f}")
    print(f"  Answer Relevancy:  {ar}")
    print(f"  Context Recall:    {cr}")
    print("=" * 60)


if __name__ == "__main__":
    main()