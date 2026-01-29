import asyncio
import httpx

async def test_amazon_income():
    url = 'http://127.0.0.1:8000/analyze'
    payload = {
        'user_input': "What was Amazon's net income in 2023?",
        'ticker': 'AMZN',
        'year': 2023
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            r = await client.post(url, json=payload)
            print(f'Status: {r.status_code}')
            if r.status_code == 200:
                data = r.json()
                print(f'Answer: {data.get("answer")}')
                print(f'\nContext used (first 2):')
                for ctx in data.get("context_used", [])[:2]:
                    print(f'  - {ctx[:200]}...')
            else:
                print(f'Error: {r.text}')
        except Exception as e:
            print(f'Exception: {e}')

if __name__ == "__main__":
    asyncio.run(test_amazon_income())
