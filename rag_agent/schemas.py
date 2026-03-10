from typing import List
from pydantic import BaseModel, Field

class QueryAnalysis(BaseModel):
    is_clear: bool = Field(
        description="Indicates if the user's question is clear and answerable."
    )
    questions: List[str] = Field(
        description="List of rewritten, self-contained questions."
    )
    clarification_needed: str = Field(
        description="Explanation if the question is unclear."
    )

class RetrievalMetrics(BaseModel):
    """Tracks retrieval quality for confidence scoring."""
    top_score: float = 0.0
    scored_chunks: int = 0
    low_confidence: bool = False