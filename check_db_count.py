import asyncio
from sqlalchemy import select, func
from app.database import init_db, AsyncSessionLocal
from app.models import Filing

async def check_ingestion_count():
    await init_db()
    async with AsyncSessionLocal() as session:
        stmt = select(func.count()).select_from(Filing).where(
            Filing.ticker == "MSFT",
            Filing.year == 2023
        )
        result = await session.execute(stmt)
        count = result.scalar()
        print(f"Total chunks for MSFT 2023: {count}")

if __name__ == "__main__":
    asyncio.run(check_ingestion_count())
