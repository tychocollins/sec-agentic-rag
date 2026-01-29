import asyncio
import httpx
from app.main import app

async def verify_classifier():
    print("--- Verifying Classifier & Natural Language API ---")
    
    # We'll use the TestClient approach or direct httpx against the running server if we could, 
    # but here we use ASGITransport for internal testing without needing the server up on port 8000
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Question with explicit context in natural language
        nl_question = "What was the revenue for Apple in 2023?"
        print(f"\nSending NL Question: '{nl_question}'")
        
        payload = {
            "user_input": nl_question
        }
        
        try:
            # We expect the classifier to pick up AAPL and 2023
            response = await client.post("/analyze", json=payload, timeout=30.0)
            
            if response.status_code == 200:
                data = response.json()
                print("\n--- Result ---")
                print(f"Ticker Used: {data.get('ticker_used')}")
                print(f"Year Used: {data.get('year_used')}")
                print(f"Answer: {data.get('answer')}")
                
                if data.get('ticker_used') == 'AAPL' and data.get('year_used') == 2023:
                    print("\nSUCCESS: Classifier correctly extracted Ticker and Year.")
                else:
                    print("\nFAIL: Classifier did not extract correct metadata.")
            else:
                print(f"FAIL: API Error {response.status_code} - {response.text}")
                
        except Exception as e:
             print(f"FAIL: Exception: {e}")

if __name__ == "__main__":
    from app.database import init_db
    asyncio.run(init_db()) # Ensure DB is ready
    asyncio.run(verify_classifier())
