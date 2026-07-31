from typing import List
from langchain_core.tools import tool
from core.logging_config import logger
from db.parent_store_manager import ParentStoreManager
from core.schemas import ErrorType
from core import observability as obs
from config import RAG_MIN_RETRIEVAL_SCORE
MIN_RETRIEVAL_SCORE = RAG_MIN_RETRIEVAL_SCORE

class ToolFactory:
    
    def __init__(self, collection):
        self.collection = collection
        self.parent_store_manager = ParentStoreManager()
    
    def _search_child_chunks(self, query: str, limit: int = 20, trace_id: str = None):
        """
        Search for the top K most relevant child chunks and log each chunk for evaluation.

        Returns:
            List[dict]: [
                {
                    "content": str,
                    "score": float,
                    "parent_id": str,
                    "source": str
                },
                ...
            ]
            Returns empty list if no results or error.
        """
        with obs.span("search_child_chunks", kind="retrieval", input_payload={"query": query, "limit": limit}) as sp:
            try:
                # similarity_search_with_score returns list of (doc, score)
                results = self.collection.similarity_search_with_score(
                    query,
                    k=limit,
                    score_threshold=0.5
                )

                # Apply score threshold explicitly — LangChain wrapper doesn't always honor it
                results = [(doc, score) for doc, score in results if score >= MIN_RETRIEVAL_SCORE]

                if not results:
                    logger.info({
                        "trace_id": trace_id,
                        "query": query,
                        "error_type": ErrorType.RETRIEVAL_EMPTY,
                        "event": "no_relevant_chunks"
                    })
                    sp.set_output({"result_count": 0})
                    return []

                structured_results = []

                for rank, (doc, score) in enumerate(results, start=1):
                    chunk_data = {
                        "content": doc.page_content.strip(),
                        "score": float(score),
                        "parent_id": doc.metadata.get("parent_id", ""),
                        "source": doc.metadata.get("source", ""),
                        "rank": rank
                    }

                    structured_results.append(chunk_data)

                    # Log each retrieved chunk
                    logger.info({
                        "trace_id": trace_id,
                        "query": query,
                        "rank": rank,
                        "score": score,
                        "parent_id": chunk_data["parent_id"],
                        "source": chunk_data["source"],
                        "chunk_preview": chunk_data["content"][:200]
                    })

                # Tag top score on first result for state propagation
                if structured_results:
                    structured_results[0]["top_score"] = structured_results[0]["score"]

                sp.set_attribute("result_count", len(structured_results))
                sp.set_attribute("top_score", structured_results[0]["score"])
                sp.set_output({
                    "result_count": len(structured_results),
                    "top_score": structured_results[0]["score"],
                    "sources": list({r["source"] for r in structured_results}),
                })

                return structured_results

            except Exception as e:
                logger.error({
                    "trace_id": trace_id,
                    "query": query,
                    "event": "retrieval_error",
                    "error": str(e)
                })
                sp.set_attribute("error", str(e))
                return []

    
    def _retrieve_many_parent_chunks(self, parent_ids: List[str]) -> str:
        """Retrieve full parent chunks by their IDs.
    
        Args:
            parent_ids: List of parent chunk IDs to retrieve
        """
        with obs.span("retrieve_many_parent_chunks", kind="retrieval", input_payload={"parent_ids": parent_ids}) as sp:
            try:
                ids = [parent_ids] if isinstance(parent_ids, str) else list(parent_ids)
                raw_parents = self.parent_store_manager.load_content_many(ids)
                if not raw_parents:
                    sp.set_output({"result_count": 0})
                    return "NO_PARENT_DOCUMENTS"

                sp.set_output({"result_count": len(raw_parents)})
                return "\n\n".join([
                    f"Parent ID: {doc.get('parent_id', 'n/a')}\n"
                    f"File Name: {doc.get('metadata', {}).get('source', 'unknown')}\n"
                    f"Content: {doc.get('content', '').strip()}"
                    for doc in raw_parents
                ])

            except Exception as e:
                sp.set_attribute("error", str(e))
                return f"PARENT_RETRIEVAL_ERROR: {str(e)}"
    
    def _retrieve_parent_chunks(self, parent_id: str) -> str:
        """Retrieve full parent chunks by their IDs.
    
        Args:
            parent_id: Parent chunk ID to retrieve
        """
        with obs.span("retrieve_parent_chunk", kind="retrieval", input_payload={"parent_id": parent_id}) as sp:
            try:
                parent = self.parent_store_manager.load_content(parent_id)
                if not parent:
                    sp.set_output({"found": False})
                    return "NO_PARENT_DOCUMENT"

                sp.set_output({"found": True, "source": parent.get("metadata", {}).get("source", "unknown")})
                return (
                    f"Parent ID: {parent.get('parent_id', 'n/a')}\n"
                    f"File Name: {parent.get('metadata', {}).get('source', 'unknown')}\n"
                    f"Content: {parent.get('content', '').strip()}"
                )

            except Exception as e:
                sp.set_attribute("error", str(e))
                return f"PARENT_RETRIEVAL_ERROR: {str(e)}"
    
    def create_tools(self) -> List:
        """Create and return the list of tools."""
        search_tool = tool("search_child_chunks")(self._search_child_chunks)
        retrieve_tool = tool("retrieve_parent_chunks")(self._retrieve_parent_chunks)
        
        return [search_tool, retrieve_tool]