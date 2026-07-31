# --- Directory Configuration ---
MARKDOWN_DIR = "markdown_docs"
PARENT_STORE_PATH = "parent_store"
QDRANT_DB_PATH = "qdrant_db"

# --- Qdrant Configuration ---
CHILD_COLLECTION = "document_child_chunks"
SPARSE_VECTOR_NAME = "sparse"

# --- Model Configuration ---
DENSE_MODEL = "sentence-transformers/all-mpnet-base-v2"
SPARSE_MODEL = "Qdrant/bm25"
LLM_MODEL = "gpt-4o-mini"
LLM_TEMPERATURE = 0

MAX_PDF_PAGES = 150

# --- RAG Configuration ---
RAG_MIN_RETRIEVAL_SCORE = 0.62

# --- Agent Loop Safety ---
# MAX_AGENT_TOOL_CALLS: soft cap enforced in rag_agent/edges.py's routing logic.
# Once the agent has made this many reasoning/tool-call passes without landing
# on a final answer, we force it to stop and fall back to
# extract_final_answer's "Unable to generate an answer." path — a graceful
# stop instead of an unbounded retry loop. Found via AgentOps trace data:
# ambiguous hash-name queries (e.g. "SHA2", "MD5") were triggering 30-100+
# passes before eventually failing on an OpenAI rate limit.
MAX_AGENT_TOOL_CALLS = 6

# RECURSION_LIMIT: hard backstop passed to LangGraph's `recursion_limit`
# config. This was previously referenced in core/rag_orchestrator.py
# (`config.RECURSION_LIMIT`) but never actually defined here — meaning it
# either raised AttributeError on every request, or a local/uncommitted
# config.py silently masked the bug. Set comfortably above
# MAX_AGENT_TOOL_CALLS so the soft cap above is what normally triggers;
# this is purely a last-resort ceiling in case some other loop path opens
# up in the future.
RECURSION_LIMIT = 30

# File validation
MAX_FILE_SIZE_MB = 50
ALLOWED_EXTENSIONS = [".pdf", ".md"]

# Cache settings
CACHE_TTL_SECONDS = 3600          # cross-session cache TTL (1 hour default)
CACHE_MAX_CROSS_SESSION = 500     # max cross-session entries before LRU eviction

# --- Text Splitter Configuration ---
CHILD_CHUNK_SIZE = 500
CHILD_CHUNK_OVERLAP = 100
MIN_PARENT_SIZE = 2000
MAX_PARENT_SIZE = 10000
HEADERS_TO_SPLIT_ON = [
    ("#", "H1"),
    ("##", "H2"),
    ("###", "H3")
]