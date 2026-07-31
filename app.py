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
    print("step 1 - starting container")
    container = AppContainer()
    container.start()
    print("step 2 - container started")
    rag_orchestrator = RAGOrchestrator(container)
    print("step 3 - orchestrator created")
    cache = ResponseCache()
    chat_service = ChatService(rag_orchestrator, cache=cache)
    print("step 4 - chat service created")
    doc_manager = DocumentManager(container)
    print("step 5 - doc manager created")
    demo = create_gradio_ui(chat_service, doc_manager)
    print("step 6 - UI created")
    print("\n🚀 Launching RAG Assistant...")
    try:
        demo.launch(css=custom_css, server_port=7861)
    except Exception as e:
        print(f"Launch error: {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")