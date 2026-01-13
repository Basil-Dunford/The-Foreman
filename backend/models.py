from pydantic import BaseModel
from typing import List, Optional

class IngestResponse(BaseModel):
    filename: str
    chunks_processed: int
    status: str

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 3

class QueryResponse(BaseModel):
    answer: str
    source_nodes: List[str]

class RiskScoutRequest(BaseModel):
    project_description: str

class RiskScoutResponse(BaseModel):
    analysis: str
    relevant_past_projects: List[str]
    risk_flags: List[str]
