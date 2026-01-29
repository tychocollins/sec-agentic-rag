from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import AnalysisRequest, AnalysisResponse
from app.models import Filing
from app.agents.planner import PlannerAgent
from app.agents.search import SearchAgent
from app.agents.reviewer import ReviewerAgent
from app.agents.utils import get_embedding, get_model

router = APIRouter()

from app.agents.classifier import ClassifierAgent
from app.agents.analyst import AnalystAgent
from app.services.ingestion_service import IngestionService

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_filing(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    # 0. Classify / Extract Metadata
    tickers = [request.ticker] if request.ticker else None
    year = request.year
    
    if not tickers or not year:
        classifier = ClassifierAgent()
        metadata = await classifier.classify(request.user_input)
        if not tickers:
            tickers = metadata.get("tickers") or [metadata.get("ticker", "UNKNOWN")]
        if not year:
            year = metadata.get("year", 2023)
            
    # Use user_input as the question if not explicitly provided
    question_text = request.question if request.question else request.user_input

    # 1. AUTO-INGEST CHECK
    ingester = IngestionService(db)
    for ticker in tickers:
        if ticker != "UNKNOWN":
            await ingester.ingest_if_missing(ticker, year)

    # 2. Plan
    planner = PlannerAgent()
    steps = await planner.plan(question_text)
    
    # 3. Search & Context Accumulation
    search_agent = SearchAgent(db)
    
    # Run searches. If a step mentions a specific company, only search that company.
    # Otherwise, search all tickers.
    search_tasks = []
    import asyncio
    
    for step in steps:
        step_lower = step.lower()
        target_tickers = []
        
        # Simple heuristic: if step mentions a ticker or company name, target it
        for t in tickers:
            if t.lower() in step_lower:
                target_tickers.append(t)
        
        # If no specific ticker found in step, or multiple found, search all
        if not target_tickers:
            target_tickers = tickers
            
        for t in target_tickers:
            search_tasks.append(search_agent.search(step, t, year, limit=10))
    
    # Run searches in parallel to cut processing time
    if search_tasks:
        try:
            all_results = await asyncio.gather(*search_tasks)
        except Exception as e:
            print(f"Error during parallel search: {e}")
            all_results = []
    else:
        all_results = []


    all_context = []
    for results in all_results:
        for res in results:
             # Prepend ticker/year to context so Analyst knows whose data it is
             context_entry = f"[{res.ticker} {res.year}] {res.text_content}"
             if context_entry not in all_context:
                 all_context.append(context_entry)
    
    if not all_context:
        return AnalysisResponse(
            answer="No relevant information found in the filings for " + ", ".join(tickers),
            steps=steps,
            context_used=[],
            ticker_used=", ".join(tickers),
            year_used=year
        )

    # 4. Generate Initial Answer (Analyst with Tools)
    analyst = AnalystAgent()
    context_str = "\n".join(all_context)
    initial_answer = await analyst.analyze(question_text, context_str)

    # 5. Review & Verify
    reviewer = ReviewerAgent()
    final_answer = await reviewer.review(question_text, initial_answer, all_context)
    
    return AnalysisResponse(
        answer=final_answer,
        steps=steps,
        context_used=all_context[:5], # Return top 5 contexts used for transparency
        ticker_used=", ".join(tickers),
        year_used=year
    )


class IngestRequest(BaseModel):
    ticker: str
    year: int
    text: Optional[str] = None
    download: bool = False


@router.post("/ingest")
async def ingest_filing(request: IngestRequest, db: AsyncSession = Depends(get_db)):
    ingester = IngestionService(db)
    
    if request.text:
        # Manual text ingestion still uses robust cleaning/chunking
        clean_text = ingester.advanced_clean(request.text)
        chunks = ingester.smart_chunk(clean_text)
        for i, chunk in enumerate(chunks):
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
        return {"message": f"Manually ingested {len(chunks)} chunks for {request.ticker} {request.year}"}
    
    # Download path
    await ingester.ingest_if_missing(request.ticker, request.year)
    return {"message": f"Processing complete for {request.ticker} {request.year}"}

