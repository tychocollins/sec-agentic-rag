from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio
import json

from app.database import get_db, AsyncSessionLocal
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

async def background_ingestion_task(ticker: str, year: int):
    """Wrapper to run full ingestion in background with its own DB session."""
    async with AsyncSessionLocal() as db:
        service = IngestionService(db)
        await service.ingest_background(ticker, year)

@router.post("/analyze")
async def analyze_filing(request: AnalysisRequest, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
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

        # 1. Plan First (Low Latency)
        planner = PlannerAgent()
        steps = await planner.plan(question_text)
        
        # 2. Send Metadata Event (IMMEDIATE FEEDBACK)
        # Context is empty initially because we haven't searched yet
        metadata_payload = {
            "type": "metadata",
            "steps": steps,
            "ticker_used": ", ".join(tickers),
            "year_used": year,
            "context_used": [] 
        }
        yield f"data: {json.dumps(metadata_payload)}\n\n"
        
        # Immediate Heartbeat to keep connection alive during I/O
        yield f"data: {json.dumps({'type': 'status', 'text': 'Locating filing and analyzing financial data... '})}\n\n"

        # 3. PRIORITY INGESTION (Split Strategy)
        ingester = IngestionService(db)
        for ticker in tickers:
            if ticker != "UNKNOWN":
                # Fast Path: Priority Chunks (Foreground, Awaited)
                # This grabs just the financial statements (~5-10 chunks) quickly
                await ingester.ingest_priority(ticker, year)
                
                # Slow Path: Full Ingestion (Background, Fire-and-Forget)
                # This processes the rest of the 10-K without blocking the user
                background_tasks.add_task(background_ingestion_task, ticker, year)

        # 4. Search & Context Accumulation
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
                # OPTIMIZATION: If the step is a generic "Directly extract" instruction, 
                # swap it for a high-precision targeted search query.
                query_text = step
                if "Directly extract" in step:
                    query_text = f"Consolidated Statements of Operations {t} {year} Revenue Net Income"
                
                search_tasks.append(search_agent.search(query_text, t, year, limit=3)) # Optimized limit
        
        if search_tasks:
            all_results = await asyncio.gather(*search_tasks)
        else:
            all_results = []

        all_context = []
        for results in all_results:
            for res in results:
                # Metadata Injection: Prepend ticker/year clearly
                context_entry = f"Context (Metadata): This data belongs to {res.ticker} for fiscal year {res.year}.\nContent: {res.text_content}"
                if context_entry not in all_context:
                    all_context.append(context_entry)
        
        if not all_context:
            yield f"data: {json.dumps({'type': 'error', 'message': 'No relevant information found'})}\n\n"
            return
            
        # 5. Yield Citations Event (Now that we have them)
        yield f"data: {json.dumps({'type': 'citations', 'context': all_context[:3]})}\n\n"

        # 4. Generate Initial Answer (OR Skip for Direct Extraction)
        # Check if we are in Direct Extraction mode (one-step plan starting with 'Directly extract')
        # DISABLE DIRECT EXTRACTION FOR NOW: It returns a placeholder. We need real analysis.
        is_direct = False # len(steps) == 1 and steps[0].startswith("Directly extract")
        
        if is_direct:
            initial_answer = f"The requested financial metric for the year {year} is being analyzed based on the 10-K filing."
        else:
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

