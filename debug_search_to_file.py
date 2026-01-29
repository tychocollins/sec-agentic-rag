import asyncio
from app.database import AsyncSessionLocal
from app.agents.search import SearchAgent
import os

# Disable individual SQL echo for this script if needed, but we can just print clearly
async def debug_search():
    async with AsyncSessionLocal() as db:
        agent = SearchAgent(db)
        
        queries = [
            "Find the total revenue for 2023",
            "Apple total net sales 2023"
        ]
        
        with open("search_debug_output.txt", "w") as f:
            for q in queries:
                f.write(f"\nQUERY: {q}\n")
                for t in ["AAPL", "MSFT"]:
                    f.write(f"  TARGET: {t}\n")
                    results = await agent.search(q, t, 2023, limit=10)
                    for r in results:
                        f.write(f"    - [{r.ticker}] {r.text_content[:200].replace('\\n', ' ')}\n")

if __name__ == "__main__":
    asyncio.run(debug_search())
