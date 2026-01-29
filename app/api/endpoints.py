from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

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

@router.post("/analyze")
async def analyze_filing(request: AnalysisRequest, db: AsyncSession = Depends(get_db)):
    async def event_generator():
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
        search_tasks = []
        
        for step in steps:
            step_lower = step.lower()
            target_tickers = []
            for t in tickers:
                if t.lower() in step_lower:
                    target_tickers.append(t)
            if not target_tickers:
                target_tickers = tickers
            for t in target_tickers:
                search_tasks.append(search_agent.search(step, t, year, limit=3)) # Optimized limit
        
        if search_tasks:
            all_results = await asyncio.gather(*search_tasks)
        else:
            all_results = []

        all_context = []
        for results in all_results:
            for res in results:
                 context_entry = f"[{res.ticker} {res.year}] {res.text_content}"
                 if context_entry not in all_context:
                     all_context.append(context_entry)
        
        if not all_context:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No relevant information found'})}\n\n"
            return

        # Send metadata event
        metadata_payload = {
            "type": "metadata",
            "steps": steps,
            "ticker_used": ", ".join(tickers),
            "year_used": year,
            "context_used": all_context[:3] # Pass a few for citations
        }
        yield f"data: {json.dumps(metadata_payload)}\n\n"

        # 4. Generate Initial Answer
        analyst = AnalystAgent()
        context_str = "\n".join(all_context)
        initial_answer = await analyst.analyze(question_text, context_str)

        # 5. Review & Verify (STREAMING)
        reviewer = ReviewerAgent()
        async for token in reviewer.stream_review(question_text, initial_answer, all_context):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        
        yield "data: {\"type\": \"done\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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

