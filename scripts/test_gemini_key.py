import asyncio
import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

async def test_key():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("FAIL: GEMINI_API_KEY not foundenv")
        return

    print(f"Testing with key ending in: ...{api_key[-4:]}")
    genai.configure(api_key=api_key)
    
    try:
        print("Listing available models...")
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"Found model: {m.name}")
        
        # Test with a standard model to be safe
        model = genai.GenerativeModel("gemini-3-flash-preview") 
        response = await model.generate_content_async("Hello")
        print("SUCCESS: Gemini Response:", response.text.strip())
    except Exception as e:
        print(f"FAIL: Error contacting Gemini: {e}")

if __name__ == "__main__":
    asyncio.run(test_key())
