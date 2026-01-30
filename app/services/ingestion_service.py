import re
import os
import time
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Filing
from app.services.sec_service import SECService
from app.agents.utils import get_embedding

class IngestionService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.sec_service = SECService()

    async def has_filing(self, ticker: str, year: int) -> bool:
        """Checks if we already have chunks for this ticker and year."""
        stmt = select(Filing.id).where(Filing.ticker == ticker, Filing.year == year).limit(1)
        result = await self.db.execute(stmt)
        return result.first() is not None

    async def _get_clean_text(self, ticker: str, year: int) -> str | None:
        """Downloads and cleans text if not found in DB."""
        print(f"Downloading 10-K for {ticker} {year}...")
        html_path = self.sec_service.download_10k(ticker, year)
        if not html_path:
            return None
        
        raw_text = self.sec_service.clean_text(html_path)
        return self.advanced_clean(raw_text)

    def _extract_priority_chunks(self, text: str) -> list[str]:
        """Extracts only keywords related to primary financial statements."""
        priority_chunks = []
        
        # Regex for "Consolidated Statements of Operations" / "Income Statements"
        # We capture the header and the following ~4000 chars (approx 1-2 pages)
        patterns = [
            r"(?i)(consolidated\s+statements?\s+of\s+(?:operations|income|earnings|comprehensive\s+income))",
            r"(?i)(summary\s+of\s+financial\s+data)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                start = match.start()
                # Grab header + context. 
                # 4000 characters is roughly 1-1.5 dense pages of text/tables
                end = min(len(text), start + 4000) 
                chunk = text[start:end].strip()
                if chunk:
                    priority_chunks.append(chunk)
                    
        return priority_chunks

    async def _ingest_chunks(self, ticker: str, year: int, chunks: list[str], start_index: int = 0):
        """Helper to embedding and save a list of chunks."""
        for i, chunk in enumerate(chunks):
            # Reduced delay for priority chunks to make it even faster
            # For background chunks, we can keep the delay
            if i > 0:
                await asyncio.sleep(0.1) 
            
            embedding = await get_embedding(chunk)
            filing = Filing(
                ticker=ticker,
                year=year,
                chunk_index=start_index + i,
                text_content=chunk,
                embedding=embedding
            )
            self.db.add(filing)
        
        await self.db.commit()

    async def ingest_priority(self, ticker: str, year: int) -> bool:
        """Fast-path: Ingest ONLY key financial statements."""
        if await self.has_filing(ticker, year):
            return True

        text = await self._get_clean_text(ticker, year)
        if not text:
            return False
            
        priority_chunks = self._extract_priority_chunks(text)
        if priority_chunks:
            print(f"[Priority] Ingesting {len(priority_chunks)} priority chunks for {ticker}...")
            await self._ingest_chunks(ticker, year, priority_chunks, start_index=0)
            return True
        else:
            print(f"[Priority] No priority sections found for {ticker}, falling back to full ingest.")
            # If we can't find priority sections, we might as well just return 
            # and let background task handle it, OR we could ingest the first few chunks.
            # For now, let's treat it as 'done' for priority purposes so we don't block.
            return True

    async def ingest_background(self, ticker: str, year: int):
        """Slow-path: Ingest the rest of the document."""
        # We check again if we need to download, but likely we just reuse the file if locally cached by download_10k logic
        # Ideally, we pass the text, but for simplicity/statelessness we re-read.
        # Check if we already have *full* coverage? 
        # For this iteration, we will naive-ingest the whole thing. 
        # Since we use append, this might create duplicates of the priority chunks in the DB 
        # if we aren't careful.
        # STRATEGY: We will ingest everything. The Priority Chunks are just "extra" copies 
        # at the beginning of the index. This acts as a boost mechanism!
        
        # Check if we already have *full* coverage (indicated by high chunk indices)
        # Priority chunks are < 1000. Background chunks are >= 1000.
        stmt = select(Filing.id).where(
            Filing.ticker == ticker, 
            Filing.year == year,
            Filing.chunk_index >= 1000
        ).limit(1)
        result = await self.db.execute(stmt)
        if result.first(): 
            print(f"[Background] Full ingestion likely complete for {ticker} {year} (found high-index chunks).")
            return

        print(f"[Background] Starting full ingestion for {ticker} {year}...")
        text = await self._get_clean_text(ticker, year)
        if not text:
            return

        chunks = self.smart_chunk(text)
        print(f"[Background] Found {len(chunks)} total chunks. Ingesting...")
        
        # We use a larger delay for background to be nice to rate limits
        for i, chunk in enumerate(chunks):
            if i > 0:
                await asyncio.sleep(2)
            
            embedding = await get_embedding(chunk)
            filing = Filing(
                # Use a high chunk index offset to avoid colliding with priority chunks 'conceptually'
                # though physically they are just rows. 
                # Actually, duplicate content is fine, it just increases recall.
                ticker=ticker,
                year=year,
                chunk_index=1000 + i, # Offset to distinguish from priority
                text_content=chunk,
                embedding=embedding
            )
            self.db.add(filing)
            
            if (i + 1) % 10 == 0:
                 # Commit internal batches to prevent massive transaction holding
                await self.db.commit()
                print(f"  [Background] Embedded {i + 1}/{len(chunks)}...")
        
        await self.db.commit()
        print(f"[Background] Completed full ingestion for {ticker} {year}.")

    # Legacy wrapper for backward compatibility if needed, or simply remove
    async def ingest_if_missing(self, ticker: str, year: int):
        await self.ingest_priority(ticker, year)
        await self.ingest_background(ticker, year)

    def advanced_clean(self, text: str) -> str:
        """Removes XBRL/XML tags and excessive whitespace."""
        # Remove XBRL tags like us-gaap:Revenue, msft:Income, etc.
        text = re.sub(r'[a-z\-]+:[a-zA-Z0-9]+', '', text)
        # Remove common SEC noise
        text = re.sub(r'http://fasb\.org/[^\s]+', '', text)
        text = re.sub(r'0000\d{6}', '', text) # Central Index Key noise
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def smart_chunk(self, text: str, chunk_size: int = 1500, overlap: int = 200) -> list[str]:
        """Splits text into overlapping chunks for better retrieval coverage."""
        chunks = []
        if not text:
            return chunks

        start = 0
        while start < len(text):
            end = start + chunk_size
            # Try to find a good breaking point (period + space)
            if end < len(text):
                last_period = text.rfind('. ', start, end)
                if last_period != -1 and last_period > start + (chunk_size // 2):
                    end = last_period + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start < 0: start = 0
            if end >= len(text): break
            
        return chunks
