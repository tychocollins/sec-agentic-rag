import asyncio
import httpx

async def test_comparison():
    url = 'http://127.0.0.1:8000/analyze'
    payload = {
        'user_input': "What was the net profit margin for both Google and Amazon in 2023? Which company was more efficient at turning revenue into profit?"
    }
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            r = await client.post(url, json=payload)
            print(f'Status: {r.status_code}')
            if r.status_code == 200:
                data = r.json()
                print(f'\nAnswer:\n{data.get("answer")}')
            else:
                print(f'Error: {r.text}')
        except Exception as e:
            print(f'Exception: {e}')

if __name__ == "__main__":
    asyncio.run(test_comparison())
