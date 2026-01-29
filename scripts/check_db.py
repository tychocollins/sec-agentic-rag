import asyncio
from app.database import AsyncSessionLocal
from app.models import Filing
from sqlalchemy import select, func

async def check():
    async with AsyncSessionLocal() as session:
        stmt = select(Filing.ticker, Filing.year, func.count(Filing.id)).group_by(Filing.ticker, Filing.year)
        result = await session.execute(stmt)
        rows = result.all()
        print("--- Database Inventory ---")
        if not rows:
            print("Database is empty.")
        for row in rows:
            print(f"Ticker: {row[0]}, Year: {row[1]}, Chunks: {row[2]}")

if __name__ == "__main__":
    asyncio.run(check())
