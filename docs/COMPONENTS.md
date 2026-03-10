# Component Explanations

## 1. AppContainer
The **AppContainer** is the infrastructure owner. It boots once at startup and holds references to every infrastructure resource:

- Qdrant vector database  
- Parent document store  
- Document chunker  
- Compiled LangGraph agent  

It registers an **`atexit` handler** to shut down cleanly when the process exits.

No other component creates infrastructure directly — everything goes through **AppContainer**.

---

## 2. ChatService
**ChatService** is the single entry point for the UI.

- Accepts **plain strings**
- Returns **plain strings**

The UI never sees **LangGraph types, LangChain objects, or Qdrant results**.

Responsibilities:

- Enforces a **90-second timeout** on all requests
- Classifies errors into structured **ErrorType categories**
- Manages the **two-tier response cache**

### ErrorType Categories

- `RETRIEVAL_EMPTY`
- `LLM_TIMEOUT`
- `GRAPH_ERROR`
- `OFF_TOPIC`
- `UNEXPECTED`

---

## 3. RAG Orchestrator
**RAGOrchestrator** owns all interaction with **LangGraph**.

Responsibilities:

- Builds the **initial graph state** from a raw query
- Runs the graph
- Streams typed **StreamEvent** objects back to ChatService

It translates between two layers:

| Layer | Representation |
|-----|-----|
| Service layer | strings, request IDs, session IDs |
| LangGraph layer | state dicts, config dicts, thread IDs |

---

## 4. LangGraph State Machine
The core of the **agentic behavior**.

LangGraph is a framework for building **stateful multi-step AI workflows as directed graphs**.

Each node reads from and writes to a shared **State object**.

### Main Graph Nodes

1. `summarize`
2. `analyze_rewrite`
3. `human_input` *(conditional interrupt)*
4. `process_question` *(agentic retrieval subgraph)*
5. `aggregate`

### Agent Subgraph (inside `process_question`)

A separate **ReAct loop** containing:

- `agent`
- `tools`
- `extract_answer`

---

## 5. Hybrid Retrieval (Qdrant)
**Qdrant** is a vector database purpose-built for similarity search.

This system uses **hybrid retrieval**, combining two strategies.

| Strategy | How It Works | Best For |
|---|---|---|
| **Dense (semantic)** | Converts text to a **768-dimensional vector**. Similar meanings produce similar vectors even with different words. | Conceptual questions — “how do I stop a leak” |
| **Sparse (BM25)** | Counts **term frequency** and **inverse document frequency**. Exact keyword matches score higher. | Specific product names — “Hydraulic Water-Stop” |
| **Hybrid (combined)** | Scores are merged using **Reciprocal Rank Fusion**. | Production use cases requiring both recall and precision |

---

## 6. Parent–Child Chunking
Splitting documents into chunks introduces a trade-off:

- **Small chunks** → precise retrieval but poor context
- **Large chunks** → strong context but imprecise retrieval

This system resolves the trade-off using a **two-level hierarchy**.

1. **Child chunks (small)** are used for retrieval  
2. When a relevant child chunk is found, its **parent chunk (large)** is retrieved  
3. The **LLM answers from the parent**, not the child

This preserves both **precision and context**.

---

## 7. ResponseCache
A **two-tier in-memory cache** with **LRU eviction** for the cross-session tier.

### Cache Key
An **MD5 hash** of the normalized query:

- Lowercased
- Stripped of extra whitespace

This ensures minor variations in capitalization or spacing still hit the cache.

### Not Cached

- Error responses
- Off-topic responses
- Low-confidence responses

---

## 8. Session Isolation (`gr.State`)
Gradio’s **`gr.State`** component creates a new value for each browser session using a **factory lambda**.

This system uses it to generate a **unique UUID per user session**.

The session ID flows through every layer:

- ChatService
- RAGOrchestrator
- LangGraph checkpointer

This guarantees that each user’s:

- Conversation history
- Cache entries
- LangGraph thread

are **fully isolated from other users**.