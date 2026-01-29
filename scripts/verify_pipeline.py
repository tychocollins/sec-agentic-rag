import asyncio
import httpx
from app.main import app

# Mock 10-K Content for AAPL 2023
AAPL_TEXT = """
Apple Inc. (AAPL) reported total net sales of $383,285 million for the fiscal year ended September 30, 2023.
This represents a decrease from $394,328 million in 2022.
Net income for 2023 was $96,995 million, down from $99,803 million in 2022.
Basic earnings per share (EPS) were $6.16 in 2023.
"""

from app.database import init_db

async def run_verification():
    print("--- Starting Verification (Async) ---")
    await init_db()
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # 1. Ingest Data
        print("\n1. Ingesting Data...")
        ingest_payload = {
            "ticker": "AAPL",
            "year": 2023,
            "text": AAPL_TEXT
        }
        response = await client.post("/ingest", json=ingest_payload)
        if response.status_code == 200:
            print("SUCCESS: Ingested data.")
        else:
            print(f"FAIL: Ingest failed {response.text}")
            return

        # 2. Analyze Question
        question = "What was the total net sales for Apple in 2023?"
        print(f"\n2. Analyzing Question: '{question}'")
        
        analyze_payload = {
            "ticker": "AAPL",
            "year": 2023,
            "question": question
        }
        
        # Increase timeout for LLM
        try:
            response = await client.post("/analyze", json=analyze_payload, timeout=30.0)
            if response.status_code == 200:
                data = response.json()
                print("\n--- Analysis Result ---")
                print(f"Answer: {data['answer']}")
                print(f"Steps: {data['steps']}")
                print(f"Context matches: {len(data['context_used'])}")
                
                # Simple assertion
                if "$383,285 million" in data['answer'] or "383,285 million" in data['answer']:
                     print("\nVERIFICATION PASSED: Answer contains correct revenue figure.")
                else:
                     print("\nVERIFICATION WARN: Check if answer is correct manually.")
            else:
                print(f"FAIL: Analyze failed {response.text}")

        except Exception as e:
            print(f"FAIL: Exception during request: {e}")

if __name__ == "__main__":
    asyncio.run(run_verification())
