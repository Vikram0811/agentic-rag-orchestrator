# Query Processing

## Step 1 — Cache Check
Before any LLM call is made, `ChatService` checks the two-tier `ResponseCache`.

**Per-session cache** checks if this exact question was asked in the current session.
**Cross-session cache** checks if any user asked this question recently within the TTL window.

Cache hits avoid the entire LangGraph pipeline, reducing latency from ~10 seconds to under **100ms**.

---

## Step 2 — Conversation Summarization
If the conversation has more than **4 messages**, the `summarize` node condenses recent history into a compact summary.

This summary is passed to **query analysis** to provide context without bloating the prompt with the full conversation history.

---

## Step 3 — Query Analysis and Rewriting
The `analyze_rewrite` node uses a **structured LLM call** to:

- Determine if the question is clear
- Detect scope ambiguity across multiple documents
- Rewrite the question into **1–3 optimized search queries**
- Identify if the user wants information across **all documents** or a **specific one**

If the question is unclear, the system returns a **clarification request** and waits via the `human_input_node` interrupt.

---

## Step 4 — Agentic Retrieval Loop

1. **Agent node** calls the LLM with the RAG agent prompt and available tools  
2. LLM calls `search_child_chunks` with an optimized query  
3. **Hybrid search** runs in Qdrant  
   - Dense semantic search  
   - Sparse BM25 search  
   - Results re-ranked by combined score  
4. **Score threshold filter** (`RAG_MIN_RETRIEVAL_SCORE = 0.62`) removes low-relevance chunks  
5. If relevant chunks are found, LLM calls `retrieve_parent_chunks` for full surrounding context  
6. LLM synthesizes an answer from the parent content  
7. If retrieval fails after **one retry**, the agent stops and reports that no relevant information was found

---

## Step 5 — Response Aggregation
The `aggregate` node:

- Collects answers from all rewritten question branches
- Deduplicates responses
- Runs a **final LLM call** to synthesize a coherent, concise answer

Additional checks:

- If the **top retrieval score < 0.4**, a **low-confidence warning** is appended
- Removes meta-language such as *"according to the documents"* from the final response

---

## Step 6 — Streaming to UI
The final answer streams **token by token** using `astream_events()` in LangGraph.

This stream feeds into **Gradio's ChatInterface** as a progressive string, allowing users to see words appear in real time instead of waiting for the full response.

---

## Step 7 — Cache Storage
After a successful response, `ChatService` stores the answer in:

- **Per-session cache**
- **Cross-session cache**

The cache is keyed by a **normalized MD5 hash of the query**.

Future identical questions from any user will be served directly from cache.