import asyncio
from app.database import AsyncSessionLocal
from app.models import Filing
from sqlalchemy import select

async def inspect():
    async with AsyncSessionLocal() as session:
        # Search for chunks that might contain income data
        stmt = select(Filing.text_content).where(
            Filing.ticker == 'AMZN',
            Filing.year == 2023
        ).limit(30)
        result = await session.execute(stmt)
        rows = result.all()
        
        print(f"--- AMZN 2023 Chunks (first 30) ---")
        for i, row in enumerate(rows):
            content = row[0]
            # Check if it mentions income-related keywords
            if 'income' in content.lower() or 'net' in content.lower() or 'revenue' in content.lower() or 'sales' in content.lower():
                print(f"\n=== CHUNK {i} (RELEVANT) ===")
                print(content[:500])
            else:
                print(f"\nCHUNK {i}: (no income keywords)")

if __name__ == "__main__":
    asyncio.run(inspect())
