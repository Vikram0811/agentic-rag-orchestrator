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
