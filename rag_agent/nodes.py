from langchain_core.messages import SystemMessage, HumanMessage, RemoveMessage, AIMessage
from .graph_state import State, AgentState
from .schemas import QueryAnalysis
from .prompts import *
import re
import time

# Confidence threshold — answers with top retrieval score below this get a disclaimer
CONFIDENCE_THRESHOLD = 0.4

def analyze_chat_and_summarize(state: State, llm):
    if len(state["messages"]) < 4:
        return {"conversation_summary": ""}

    relevant_msgs = [
        msg for msg in state["messages"][:-1]
        if isinstance(msg, (HumanMessage, AIMessage))
        and not getattr(msg, "tool_calls", None)
    ]

    if not relevant_msgs:
        return {"conversation_summary": ""}

    conversation = "Conversation history:\n"
    for msg in relevant_msgs[-6:]:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant"
        conversation += f"{role}: {msg.content}\n"

    summary_response = llm.with_config(temperature=0.2).invoke(
        [SystemMessage(content=get_conversation_summary_prompt())] +
        [HumanMessage(content=conversation)]
    )
    return {"conversation_summary": summary_response.content, "agent_answers": [{"__reset__": True}]}


from pathlib import Path


def analyze_and_rewrite_query(state: 'State', llm):
    last_message = state["messages"][-1]
    conversation_summary = state.get("conversation_summary", "")
    document_count = state.get("document_count", 1)
    document_names = [Path(fname).stem.lower() for fname in state.get("document_names", [])]

    # -----------------------------
    # 1️⃣ Deterministic scope clarification
    # -----------------------------
    if document_count > 1:
        query_lower = last_message.content.lower().strip()

        ambiguous_scope = (
            "document" in query_lower
            and "all" not in query_lower
            and not any(fname in query_lower for fname in document_names)
        )

        if ambiguous_scope:
            return {
                "questionIsClear": False,
                "messages": [AIMessage(
                    content=(
                        "Multiple documents are uploaded. "
                        "Would you like a summary of all documents or a specific file? "
                        "Please specify by filename or say 'all'."
                    )
                )],
                "all_documents_intent": False
            }

    # -----------------------------
    # 2️⃣ Only call LLM if scope is clear
    # -----------------------------
    context_section = (
        f"Conversation Context:\n{conversation_summary}\n" if conversation_summary.strip() else ""
    ) + f"User Query:\n{last_message.content}\n"

    llm_with_structure = llm.with_config(temperature=0.1).with_structured_output(QueryAnalysis)
    response = llm_with_structure.invoke(
        [SystemMessage(content=get_query_analysis_prompt()),
         HumanMessage(content=context_section)]
    )

    # -----------------------------
    # 3️⃣ Clear query path
    # -----------------------------
    if len(response.questions) > 0 and response.is_clear:
        last_human_id = last_message.id
        delete_all = [
            RemoveMessage(id=m.id)
            for m in state["messages"]
            if not isinstance(m, SystemMessage) and m.id != last_human_id
        ]

        all_docs_flag = "all" in last_message.content.lower()

        return {
            "questionIsClear": True,
            "messages": delete_all,
            "originalQuery": last_message.content,
            "rewrittenQuestions": response.questions,
            "all_documents_intent": all_docs_flag
        }

    # -----------------------------
    # 4️⃣ LLM could not clarify — fallback
    # -----------------------------
    clarification = (
        response.clarification_needed
        if response.clarification_needed and len(response.clarification_needed.strip()) > 10
        else "I need more information to understand your question."
    )

    return {
        "questionIsClear": False,
        "messages": [AIMessage(content=clarification)],
        "all_documents_intent": False
    }


def human_input_node(state: State):
    return {}


def agent_node(state: AgentState, llm_with_tools):
    sys_msg = SystemMessage(content=get_rag_agent_prompt())
    t0 = time.monotonic()

    if not state.get("messages"):
        human_msg = HumanMessage(content=state["question"])
        response = llm_with_tools.invoke([sys_msg] + [human_msg])
        retrieval_ms = int((time.monotonic() - t0) * 1000)
        return {"messages": [human_msg, response], "retrieval_ms": retrieval_ms}

    response = llm_with_tools.invoke([sys_msg] + state["messages"])
    retrieval_ms = int((time.monotonic() - t0) * 1000)
    return {"messages": [response], "retrieval_ms": retrieval_ms}


def extract_final_answer(state: AgentState):
    # Get top retrieval score from tool messages
    top_score = 0.0
    for msg in state["messages"]:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            continue
        content = getattr(msg, "content", [])
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and "top_score" in block:
                    top_score = max(top_score, float(block.get("top_score", 0.0)))

    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            return {
                "final_answer": msg.content,
                "agent_answers": [{
                    "index": state["question_index"],
                    "question": state["question"],
                    "answer": msg.content,
                    "top_score": top_score      # carry score in the dict
                }]
            }
    return {
        "final_answer": "Unable to generate an answer.",
        "agent_answers": [{
            "index": state["question_index"],
            "question": state["question"],
            "answer": "Unable to generate an answer.",
            "top_score": 0.0
        }]
    }


def aggregate_responses(state: 'State', llm):
    if not state.get("agent_answers"):
        return {"messages": [AIMessage(content="No answers were generated.")]}

    sorted_answers = sorted(state["agent_answers"], key=lambda x: x.get("index", 0))
    combined_answers = ""
    low_confidence = False
    seen = set()                                          # deduplication

    for ans in sorted_answers:
        text = ans.get("answer", "").strip()
        if not text or text in ["NO_RELEVANT_CHUNKS", "PARENT_RETRIEVAL_ERROR"]:
            low_confidence = True
            continue

        text = re.sub(r"\*\*Sources:\*\*.*", "", text, flags=re.DOTALL).strip()

        if text in seen:                                  # skip duplicates
            continue
        seen.add(text)
        combined_answers += f"{text}\n\n"

    if not combined_answers.strip():
        return {"messages": [AIMessage(content="No relevant information was found for your query.")]}
    
    # Confidence scoring
    # Compute top score directly from agent_answers — no state propagation needed
    all_scores = [
        ans.get("top_score", 0.0)
        for ans in sorted_answers
        if isinstance(ans.get("top_score"), float)
    ]
    top_score = max(all_scores) if all_scores else 0.0
    is_low_confidence = low_confidence or (0.0 < top_score < CONFIDENCE_THRESHOLD)

    user_content = (
        f"Original user question: {state.get('originalQuery', '')}\n"
        f"Retrieved answers:\n{combined_answers}"
    )

    # Single timed LLM call — was incorrectly called twice before
    t0 = time.monotonic()
    synthesis_response = llm.invoke(
        [SystemMessage(content=get_aggregation_prompt()),
         HumanMessage(content=user_content)]
    )
    generation_ms = int((time.monotonic() - t0) * 1000)

    document_count = state.get("document_count", 1)
    all_docs_intent = state.get("all_documents_intent", False)
    show_sources = document_count > 1 and all_docs_intent

    sources_section = ""
    if show_sources:
        doc_names = sorted(state.get("document_names", []))
        if doc_names:
            sources_section = "\n".join(f"- {fname}" for fname in doc_names)

    final_content = synthesis_response.content.strip()

    if sources_section:
        final_content += f"\n\n---\n**Sources:**\n{sources_section}"

    if is_low_confidence:
        final_content += (
            "\n\n> ⚠️ *This answer is based on limited matches in the knowledge base. "
            "Please verify before relying on it.*"
        )

    return {
        "messages": [AIMessage(content=final_content)],
        "generation_ms": generation_ms
    }