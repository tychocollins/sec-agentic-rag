from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models import Filing
from app.agents.utils import get_embedding
import re
import asyncio


class SearchAgent:
    def __init__(self, db: AsyncSession):
        self.db = db

    def _financial_boost(self, text_content: str) -> float:
        """
        Returns a boost factor for chunks containing financial data.
        Chunks with $ signs, large numbers, and table-like structures get higher scores.
        """
        boost = 1.0
        
        # Count dollar signs (strong indicator of financial data)
        dollar_count = text_content.count('$')
        if dollar_count >= 5:
            boost += 0.5
        elif dollar_count >= 2:
            boost += 0.3
        
        # Count large numbers (millions/billions patterns)
        large_numbers = re.findall(r'\d{1,3}(?:,\d{3})+|\d+\.\d+\s*(?:million|billion)?', text_content, re.IGNORECASE)
        if len(large_numbers) >= 3:
            boost += 0.4
        
        # Boost for income statement keywords
        income_keywords = ['net income', 'net sales', 'total revenue', 'operating income', 'gross profit', 'earnings per share', 'diluted']
        for kw in income_keywords:
            if kw in text_content.lower():
                boost += 0.2
                break
        
        return boost

    async def search(self, query: str, ticker: str, year: int, limit: int = 5) -> list[Filing]:
        """
        Performs hybrid search (Vector + Keyword) using Reciprocal Rank Fusion (RRF)
        with financial data boosting.
        """
        # 1. Vector Search
        query_embedding = await get_embedding(query)
        vector_stmt = (
            select(Filing)
            .where(Filing.ticker == ticker, Filing.year == year)
            .order_by(Filing.embedding.l2_distance(query_embedding))
            .limit(limit * 3)  # Fetch more for re-ranking
        )
        vector_results = (await self.db.execute(vector_stmt)).scalars().all()

        # 2. Keyword Search (using ts_rank)
        keyword_stmt = (
            select(Filing)
            .where(
                Filing.ticker == ticker, 
                Filing.year == year,
                text("search_vector @@ plainto_tsquery('english', :query)")
            )
            .order_by(text("ts_rank(search_vector, plainto_tsquery('english', :query)) DESC"))
            .limit(limit * 3)
        )
        keyword_results = (await self.db.execute(keyword_stmt, {"query": query})).scalars().all()

        # 3. RRF (Reciprocal Rank Fusion) with Financial Boosting
        k = 60
        scores = {}
        
        def process_results(results, weight=1.0):
            for rank, item in enumerate(results):
                if item.id not in scores:
                    scores[item.id] = {"item": item, "score": 0.0}
                # Apply financial boost to the RRF score
                financial_mult = self._financial_boost(item.text_content)
                scores[item.id]["score"] += weight * (1 / (k + rank + 1)) * financial_mult

        process_results(vector_results)
        process_results(keyword_results)
        
        # Sort by score DESC
        sorted_items = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        
        # Return top N
        return [x["item"] for x in sorted_items[:limit]]

    async def search_multi(self, query: str, tickers: list[str], year: int, limit: int = 5) -> dict[str, list[Filing]]:
        """
        Performs parallel search for multiple tickers using asyncio.gather.
        Useful for comparison queries.
        """
        tasks = [self.search(query, ticker, year, limit) for ticker in tickers]
        results = await asyncio.gather(*tasks)
        return dict(zip(tickers, results))
