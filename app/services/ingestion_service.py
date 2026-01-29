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

    async def ingest_if_missing(self, ticker: str, year: int):
        """Downloads and ingests filing only if not present."""
        if await self.has_filing(ticker, year):
            print(f"Filing for {ticker} {year} already exists in database.")
            return

        print(f"Filing for {ticker} {year} missing. Starting auto-ingestion...")
        html_path = self.sec_service.download_10k(ticker, year)
        if not html_path:
            print(f"Failed to download 10-K for {ticker} {year}.")
            return

        raw_text = self.sec_service.clean_text(html_path)
        # Apply additional robust cleaning to remove XML/XBRL noise
        clean_text = self.advanced_clean(raw_text)
        
        chunks = self.smart_chunk(clean_text)
        
        for i, chunk in enumerate(chunks):
            # Rate limit: 2s delay between embeddings to stay under Gemini free tier limits
            if i > 0:
                await asyncio.sleep(2)
            
            embedding = await get_embedding(chunk)
            filing = Filing(
                ticker=ticker,
                year=year,
                chunk_index=i,
                text_content=chunk,
                embedding=embedding
            )
            self.db.add(filing)
            
            if (i + 1) % 10 == 0:
                print(f"  Embedded {i + 1}/{len(chunks)} chunks...")
        
        await self.db.commit()
        print(f"Successfully ingested {len(chunks)} chunks for {ticker} {year}.")

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
