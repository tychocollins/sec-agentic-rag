import asyncio
import httpx
from app.database import init_db

async def verify_ingest_download():
    print("--- Testing API Ingestion with Download ---")
    
    # We need DB to be ready
    await init_db()
    
    # Target: MSFT 2023
    ticker = "MSFT"
    year = 2023
    
    print(f"Triggering ingestion for {ticker} {year}...")
    
    async with httpx.AsyncClient(base_url="http://localhost:8000", timeout=300.0) as client:

        try:
            payload = {
                "ticker": ticker,
                "year": year,
                "download": True
            }
            response = await client.post("/ingest", json=payload)
            
            if response.status_code == 200:
                print(f"SUCCESS: API returned 200")
                print(f"Response: {response.json()}")
            else:
                print(f"FAIL: API returned {response.status_code}")
                print(f"Response: {response.text}")
                
        except httpx.RequestError as e:
            print(f"FAIL: Could not connect to API: {e}")

if __name__ == "__main__":
    asyncio.run(verify_ingest_download())
