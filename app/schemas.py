from pydantic import BaseModel
from typing import List, Optional

class AnalysisRequest(BaseModel):
    ticker: str
    year: int
    question: str

class AnalysisResponse(BaseModel):
    answer: str
    steps: List[str]
    context_used: List[str]
