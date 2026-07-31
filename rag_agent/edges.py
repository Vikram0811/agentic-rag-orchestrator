from typing import Literal
from langgraph.types import Send
from langgraph.graph import END
from langgraph.prebuilt import tools_condition
from .graph_state import State, AgentState
import config

def route_after_rewrite(state: State) -> Literal["human_input", "process_question"]:
    if not state.get("questionIsClear", False):
        return "human_input"
    else:
        return [
                Send("process_question", {"question": query, "question_index": idx, "messages": []})
                for idx, query in enumerate(state["rewrittenQuestions"])
            ]


def route_agent_or_stop(state: AgentState) -> Literal["tools", "__end__"]:
    """
    Wraps LangGraph's built-in `tools_condition` with a hard soft-cap on
    agent<->tools iterations.

    Why: without this, an ambiguous query (e.g. "SHA2" when the source doc
    only lists "SHA-256"/"SHA-512") can make the agent retry many search
    phrasings indefinitely — observed via AgentOps traces hitting 30-100+
    tool calls on a single question before eventually failing on an OpenAI
    rate limit, rather than gracefully giving up. Once tool_call_count
    reaches config.MAX_AGENT_TOOL_CALLS, we force routing to END regardless
    of whether the LLM still wants to call a tool. extract_final_answer
    already has a graceful fallback ("Unable to generate an answer.") for
    exactly this case — this just makes sure we actually reach it.
    """
    if state.get("tool_call_count", 0) >= config.MAX_AGENT_TOOL_CALLS:
        return END
    return tools_condition(state)