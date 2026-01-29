import asyncio
from app.database import AsyncSessionLocal
from app.models import Filing
from sqlalchemy import delete

async def run():
    async with AsyncSessionLocal() as db:
        await db.execute(delete(Filing).where(Filing.ticker == 'META', Filing.year == 2023))
        await db.commit()
        print('Deleted META 2023 data for re-ingestion.')

if __name__ == "__main__":
    asyncio.run(run())
