import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import init_db, AsyncSessionLocal
from app.agents.search import SearchAgent

async def verify_hybrid_search():
    print("--- Verifying Hybrid Search ---")
    await init_db()
    
    async with AsyncSessionLocal() as session:
        search_agent = SearchAgent(session)
        
        # Test Query: A specific number that requires keyword matching
        query = "383,285" 
        ticker = "AAPL" # We ingested AAPL synthesized data earlier

        year = 2023
        
        print(f"Searching for '{query}' in {ticker} {year}...")
        results = await search_agent.search(query, ticker, year)
        
        print(f"Found {len(results)} results.")
        
        found = False
        for res in results:
            if "383,285" in res.text_content:
                print(f"SUCCESS: Found exact match in chunk {res.chunk_index}")
                found = True
                break
        
        if not found:
            print("FAIL: Did not find the exact number match.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    asyncio.run(verify_hybrid_search())
