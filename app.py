"""
app.py — entry point.

Boots the AppContainer (infrastructure), wires service layers,
launches Gradio.  Shutdown is registered via atexit inside AppContainer.
"""
from dotenv import load_dotenv
load_dotenv()  # reads .env and sets environment variables

import warnings
warnings.filterwarnings("ignore", message="Pydantic serializer warnings")

from core.response_cache import ResponseCache
from core.app_container import AppContainer
from core.rag_orchestrator import RAGOrchestrator
from core.chat_service import ChatService
from core.document_manager import DocumentManager
from ui.gradio_app import create_gradio_ui
from ui.css import custom_css

if __name__ == "__main__":
    # 1. Infrastructure
    container = AppContainer()
    container.start()

    # 2. Service layer
    rag_orchestrator = RAGOrchestrator(container)
    cache = ResponseCache()
    chat_service = ChatService(rag_orchestrator, cache=cache)
    doc_manager = DocumentManager(container)   # see note below

    # 3. UI — knows only about service layer
    demo = create_gradio_ui(chat_service, doc_manager)

    print("\n🚀 Launching RAG Assistant...")
    demo.launch(css=custom_css)