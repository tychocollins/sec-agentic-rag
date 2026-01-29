import asyncio
from app.database import AsyncSessionLocal
from app.agents.search import SearchAgent

async def debug_search():
    async with AsyncSessionLocal() as db:
        agent = SearchAgent(db)
        
        queries = [
            "Find the total revenue for 2023",
            "Apple total net sales 2023",
            "Microsoft total revenue 2023"
        ]
        
        tickers = ["AAPL", "MSFT"]
        
        for q in queries:
            print(f"\nQUERY: {q}")
            for t in tickers:
                print(f"  TARGET: {t}")
                results = await agent.search(q, t, 2023, limit=5)
                if not results:
                    print("    NO RESULTS FOUND")
                for r in results:
                    print(f"    - [{r.ticker}] {r.text_content[:150]}...")

if __name__ == "__main__":
    asyncio.run(debug_search())
