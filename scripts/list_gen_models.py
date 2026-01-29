import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

async def list_gen_models():
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    print("Listing generation models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found model: {m.name}")

if __name__ == "__main__":
    asyncio.run(list_gen_models())
