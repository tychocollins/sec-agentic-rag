import asyncio
import sys
import argparse
from app.database import AsyncSessionLocal
from app.services.ingestion_service import IngestionService

async def bulk_ingest(tickers: list[str], year: int):
    async with AsyncSessionLocal() as db:
        ingester = IngestionService(db)
        for ticker in tickers:
            ticker = ticker.strip().upper()
            print(f"\n--- Processing {ticker} {year} ---")
            try:
                await ingester.ingest_if_missing(ticker, year)
            except Exception as e:
                print(f"Failed to ingest {ticker}: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk ingest SEC filings into the database.")
    parser.add_argument("tickers", help="Comma-separated list of tickers (e.g., AAPL,MSFT,GOOGL)")
    parser.add_argument("--year", type=int, default=2023, help="Fiscal year to ingest (default: 2023)")
    
    args = parser.parse_args()
    
    ticker_list = args.tickers.split(",")
    asyncio.run(bulk_ingest(ticker_list, args.year))
