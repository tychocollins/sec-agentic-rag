from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas import AnalysisRequest, AnalysisResponse
from app.models import Filing
from app.agents.planner import PlannerAgent
from app.agents.search import SearchAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.utils import get_embedding, get_model

router = APIRouter()

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_filing(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    # 1. Plan
    planner = PlannerAgent()
    steps = await planner.plan(request.question)
    
    # 2. Search & Context Accumulation
    search_agent = SearchAgent(db)
    all_context = []
    
    # For a real agentic loop, we might iterate and refine. 
    # Here we just gather context for all steps.
    for step in steps:
        results = await search_agent.search(step, request.ticker, request.year)
        for res in results:
             # De-duplicate based on some criteria if needed, simple accumulation for now
             if res.text_content not in all_context:
                 all_context.append(res.text_content)
    
    if not all_context:
        return AnalysisResponse(
            answer="No relevant information found in the filings.",
            steps=steps,
            context_used=[]
        )

    # 3. Generate Initial Answer (Synthesis)
    model = get_model()
    context_str = "\n\n".join(all_context)
    synthesis_prompt = f"""
    Answer the user's question based on the context provided.
    
    Question: {request.question}
    Context: {context_str}
    
    Answer:
    """
    synthesis_response = await model.generate_content_async(synthesis_prompt)
    initial_answer = synthesis_response.text

    # 4. Review & Verify
    reviewer = ReviewerAgent()
    final_answer = await reviewer.review(request.question, initial_answer, all_context)
    
    return AnalysisResponse(
        answer=final_answer,
        steps=steps,
        context_used=all_context[:5] # Return top 5 contexts used for transparency
    )

class IngestRequest(BaseModel):
    ticker: str
    year: int
    text: str


@router.post("/ingest")
async def ingest_filing(request: IngestRequest, db: AsyncSession = Depends(get_db)):
    # Simple chunking by paragraph or character limit
    # For 10-Ks, careful chunking is key, but for this demo/MVP we split by double newline
    chunks = request.text.split("\n\n")
    
    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
            
        embedding = await get_embedding(chunk)
        
        filing = Filing(
            ticker=request.ticker,
            year=request.year,
            chunk_index=i,
            text_content=chunk,
            embedding=embedding
        )
        db.add(filing)
    
    await db.commit()
    return {"message": f"Ingested {len(chunks)} chunks for {request.ticker} {request.year}"}
