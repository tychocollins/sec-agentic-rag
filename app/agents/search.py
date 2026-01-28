from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Filing
from app.agents.utils import get_embedding

class SearchAgent:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def search(self, query: str, ticker: str, year: int, limit: int = 5) -> list[Filing]:
        # Generate embedding for the query
        query_embedding = await get_embedding(query)

        # Perform similarity search using pgvector
        # Note: Using l2_distance (<-> operator) and ordering by it
        stmt = (
            select(Filing)
            .where(Filing.ticker == ticker, Filing.year == year)
            .order_by(Filing.embedding.l2_distance(query_embedding))
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
