import asyncio
import httpx

async def query(client, url, ticker, year, question):
    print(f"\nTesting {ticker} {year}: {question}")
    payload = {
        "user_input": question,
        "ticker": ticker,
        "year": year
    }
    try:
        response = await client.post(url, json=payload)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print(f"Answer: {response.json().get('answer')}")
        else:
            print(f"Error Body: {response.text}")
    except Exception as e:
        print(f"Request Exception: {e}")

async def verify_auto_ingest():
    url = "http://127.0.0.1:8000/analyze"
    async with httpx.AsyncClient(timeout=180.0) as client:
        # 1. Microsoft (Should use re-ingested clean data)
        await query(client, url, "MSFT", 2023, "What was Microsoft's revenue in 2023?")
        
        # 2. Tesla (Should already be ingested from previous run)
        await query(client, url, "TSLA", 2023, "How much did Tesla spend on R&D in 2023?")
        
        # 3. Apple (Should already be ingested from previous run)
        await query(client, url, "AAPL", 2023, "What was Apple's net sales in 2023?")
        
        # 4. Meta (CRITICAL: Should auto-ingest correct 2023 filing now)
        await query(client, url, "META", 2023, "What is Meta's 2023 net income in billions?")

if __name__ == "__main__":
    asyncio.run(verify_auto_ingest())
