"""
DocumentManager — handles document ingestion and knowledge base management.

Now accepts AppContainer instead of the old RAGSystem, but internal logic
is unchanged.  The UI calls this via DocumentManager only.
"""
from pathlib import Path
import shutil
import config
from util import pdfs_to_markdowns


class DocumentManager:

    def __init__(self, container):
        """
        container: AppContainer
        Replaces the old RAGSystem dependency.
        """
        self._container = container
        self.markdown_dir = Path(config.MARKDOWN_DIR)
        self.markdown_dir.mkdir(parents=True, exist_ok=True)


    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def _validate_file(self, path: str) -> tuple[bool, str]:
        """
        Returns (is_valid, error_message).
        Checks file extension and size against config limits.
        """
        p = Path(path)

        if p.suffix.lower() not in config.ALLOWED_EXTENSIONS:
            return False, f"'{p.name}' skipped — unsupported type '{p.suffix}'. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"

        size_mb = p.stat().st_size / (1024 * 1024)
        if size_mb > config.MAX_FILE_SIZE_MB:
            return False, f"'{p.name}' skipped — file size {size_mb:.1f}MB exceeds {config.MAX_FILE_SIZE_MB}MB limit"

        return True, ""

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def add_documents(self, document_paths, progress_callback=None):
        if not document_paths:
            return 0, 0, []

        document_paths = (
            [document_paths] if isinstance(document_paths, str) else document_paths
        )

        # Ensure all paths are strings — Gradio may pass file objects
        document_paths = [
            str(p) if not isinstance(p, str) else p
            for p in document_paths
            if p is not None
        ]

        if not document_paths:
            return 0, 0, []

        added = 0
        skipped = 0
        validation_errors = []

        for i, doc_path in enumerate(document_paths):
            if progress_callback:
                progress_callback(
                    (i + 1) / len(document_paths),
                    f"Processing {Path(doc_path).name}",
                )

            # Validate before processing — catches bad type and size
            is_valid, error_msg = self._validate_file(doc_path)
            if not is_valid:
                validation_errors.append(error_msg)
                skipped += 1
                continue

            doc_name = Path(doc_path).stem
            md_path = self.markdown_dir / f"{doc_name}.md"

            if md_path.exists():
                skipped += 1
                continue

            try:
                if Path(doc_path).suffix.lower() == ".md":
                    shutil.copy(doc_path, md_path)
                else:
                    pdfs_to_markdowns(str(doc_path), overwrite=False)

                parent_chunks, child_chunks = self._container.chunker.create_chunks_single(md_path)

                if not child_chunks:
                    skipped += 1
                    continue

                collection = self._container.vector_db.get_collection(config.CHILD_COLLECTION)
                collection.add_documents(child_chunks)
                self._container.parent_store.save_many(parent_chunks)
                added += 1

            except Exception as e:
                validation_errors.append(f"'{Path(doc_path).name}' error — {str(e)}")
                skipped += 1

        return added, skipped, validation_errors

    def get_markdown_files(self):
        if not self.markdown_dir.exists():
            return []
        return sorted([p.name.replace(".md", ".pdf") for p in self.markdown_dir.glob("*.md")])

    def clear_all(self):
        if self.markdown_dir.exists():
            shutil.rmtree(self.markdown_dir)
            self.markdown_dir.mkdir(parents=True, exist_ok=True)

        self._container.parent_store.clear_store()
        self._container.vector_db.delete_collection(config.CHILD_COLLECTION)
        self._container.vector_db.create_collection(config.CHILD_COLLECTION)