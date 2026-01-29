from pydantic import BaseModel
from typing import List, Optional

class AnalysisRequest(BaseModel):
    user_input: str
    ticker: Optional[str] = None
    year: Optional[int] = None
    # question field is now redundant if we treat user_input as the question, 
    # but we can keep it optional for backward compatibility or removal
    question: Optional[str] = None 

class AnalysisResponse(BaseModel):
    answer: str
    steps: List[str]
    context_used: List[str]
    # Meta info to show what the classifier found
    ticker_used: str 
    year_used: int
