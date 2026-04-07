"""
Gradio UI — knows nothing about LangGraph, Qdrant, or LangChain.
"""
import gradio as gr
import uuid
from core.chat_service import ChatService
from core.document_manager import DocumentManager


def create_gradio_ui(chat_service: ChatService, doc_manager: DocumentManager):

    def clean_name(f):
        return f.replace(".md", "").replace(".pdf", "").replace("_", " ")

    def format_file_list():
        files = doc_manager.get_markdown_files()
        if not files:
            return "📭 No documents available in the knowledge base"
        return "\n".join(f"{i+1}. {clean_name(f)}" for i, f in enumerate(files))

    def upload_handler(files, progress=gr.Progress(track_tqdm=True)):
        if not files:
            return None, format_file_list(), format_file_list()
        added, skipped, errors = doc_manager.add_documents(
            files,
            progress_callback=lambda p, desc: progress(p, desc=desc)
        )
        if errors:
            for error in errors:
                gr.Warning(error)
        gr.Info(f"✅ Added: {added} | Skipped: {skipped}")
        file_list_str = format_file_list()
        return None, file_list_str, file_list_str

    def clear_handler():
        doc_manager.clear_all()
        gr.Info("🗑️ Knowledge base cleared")
        file_list_str = format_file_list()
        return file_list_str, file_list_str

    def clear_chat_handler(session_id: str):
        chat_service.reset_session(session_id)
        return [], format_file_list()

    async def stream_fn(message, history, session_id: str):
        async for chunk in chat_service.stream_ask(message, session_id):
            yield chunk

    with gr.Blocks(title="Agentic RAG Orchestrator") as demo:

        gr.Markdown("# Agentic RAG Orchestrator")
        gr.Markdown("Enterprise knowledge retrieval")

        # One gr.State per browser session — Gradio creates a new instance per user
        session_state = gr.State(lambda: str(uuid.uuid4()))

        with gr.Tab("💬 Chat"):
            chat_doc_status = gr.Textbox(
                value=format_file_list(),
                interactive=False,
                lines=3,
                label="📂 Knowledge Base",
                show_label=True,
            )
            chatbot = gr.Chatbot(
                height=500,
                placeholder="Ask me anything about your documents!",
                show_label=False,
            )
            new_conversation_btn = gr.Button("🔄 New Conversation", variant="secondary", size="md")
            gr.ChatInterface(
                fn=stream_fn,
                chatbot=chatbot,
                additional_inputs=[session_state]
            )

            new_conversation_btn.click(
                clear_chat_handler,
                inputs=[session_state],
                outputs=[chatbot, chat_doc_status]
            )

        with gr.Tab("📂 Documents"):
            gr.Markdown("### Upload PDF files")
            files_input = gr.File(
                file_count="multiple",
                type="filepath",
                height=150,
                show_label=False,
            )
            add_btn = gr.Button("Add to Knowledge Base", variant="primary")
            gr.Markdown("### Knowledge Base")
            file_list = gr.Textbox(
                value=format_file_list(),
                interactive=False,
                lines=8,
                show_label=False,
                elem_id="file-list-box",
            )
            with gr.Row():
                refresh_btn = gr.Button("Refresh")
                clear_btn = gr.Button("Clear All", variant="stop")

            add_btn.click(
                upload_handler,
                inputs=[files_input],
                outputs=[files_input, file_list, chat_doc_status],
                show_progress="full",
            )
            refresh_btn.click(format_file_list, None, file_list)
            clear_btn.click(clear_handler, None, [file_list, chat_doc_status])

    return demo