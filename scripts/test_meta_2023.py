import asyncio
import httpx

async def run():
    url = 'http://127.0.0.1:8000/analyze'
    payload = {
        'user_input': "What is Meta's 2023 net income in billions?",
        'ticker': 'META',
        'year': 2023
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            r = await client.post(url, json=payload)
            print(f'Status: {r.status_code}')
            if r.status_code == 200:
                print(f'Answer: {r.json().get("answer")}')
            else:
                print(f'Error: {r.text}')
        except Exception as e:
            print(f'Exception: {e}')

if __name__ == "__main__":
    asyncio.run(run())
