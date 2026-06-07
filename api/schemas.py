from pydantic import BaseModel
from typing import List, Optional

class QueryRequest(BaseModel):
    question: str
    include_eval: bool = True

class QueryResponse(BaseModel):
    answer: str
    citations: List[str]
    confidence_score: float
    conflicts_detected: bool
    conflict_details: Optional[str]
    eval_scores: Optional[dict]
    latency_ms: float