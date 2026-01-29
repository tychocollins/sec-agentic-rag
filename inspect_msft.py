import asyncio
from app.database import AsyncSessionLocal
from app.models import Filing
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as session:
        stmt = select(Filing.text_content).where(Filing.ticker == 'MSFT', Filing.year == 2023).limit(20)
        result = await session.execute(stmt)
        rows = result.all()
        print(f"--- MSFT 2023 Chunks ---")
        for i, row in enumerate(rows):
            print(f"CHUNK {i}: {row[0][:300]}...")

if __name__ == "__main__":
    asyncio.run(check())
