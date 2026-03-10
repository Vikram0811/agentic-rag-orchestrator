"""
AppContainer — single owner of all infrastructure resources.

Responsibilities:
- Construct all clients once at startup
- Expose them to the layers that need them
- Shut down cleanly on exit (no silent GC destructors)

Nothing outside this module should instantiate Qdrant, OpenAI, or the
chunker directly.
"""
import atexit
import uuid
from langchain_openai import ChatOpenAI

import config
from db.vector_db_manager import VectorDbManager
from db.parent_store_manager import ParentStoreManager
from document_chunker import DocumentChuncker
from rag_agent.tools import ToolFactory
from rag_agent.graph import create_agent_graph
from core.logging_config import logger


class AppContainer:
    """
    Singleton-style container.  Instantiate once in app.py, pass it around.
    """

    def __init__(self):
        self._started = False
        self.vector_db: VectorDbManager = None
        self.parent_store: ParentStoreManager = None
        self.chunker: DocumentChuncker = None
        self.agent_graph = None
        self._llm: ChatOpenAI = None

    # ------------------------------------------------------------------
    # Startup
    # ------------------------------------------------------------------

    def start(self):
        if self._started:
            return

        logger.info("app_container_starting")

        self.vector_db = VectorDbManager()
        self.parent_store = ParentStoreManager()
        self.chunker = DocumentChuncker()

        self.vector_db.create_collection(config.CHILD_COLLECTION)
        collection = self.vector_db.get_collection(config.CHILD_COLLECTION)

        self._llm = ChatOpenAI(
            model=config.LLM_MODEL,
            temperature=config.LLM_TEMPERATURE,
        )
        tools = ToolFactory(collection).create_tools()
        self.agent_graph = create_agent_graph(self._llm, tools)

        # Register clean shutdown — fires on normal process exit
        atexit.register(self.shutdown)

        self._started = True
        logger.info("app_container_started")

    # ------------------------------------------------------------------
    # Thread management
    # ------------------------------------------------------------------

    def get_config(self, session_id: str) -> dict:
        return {"configurable": {"thread_id": session_id}}

    def reset_thread(self, session_id: str):
        try:
            self.agent_graph.checkpointer.delete_thread(session_id)
        except Exception as e:
            logger.warning("thread_delete_failed", extra={"error": str(e)})

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def shutdown(self):
        if not self._started:
            return
        logger.info("app_container_shutting_down")
        try:
            if self.vector_db:
                self.vector_db.close()          # add close() to VectorDbManager — see note below
        except Exception as e:
            logger.warning("qdrant_close_failed", extra={"error": str(e)})
        self._started = False
        logger.info("app_container_shutdown_complete")