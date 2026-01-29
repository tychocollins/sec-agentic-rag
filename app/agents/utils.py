import os
import asyncio
import google.generativeai as genai
from google.api_core import exceptions
from google.generativeai.types import RequestOptions
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

# Extended timeout for complex comparison queries (5 minutes)
REQUEST_TIMEOUT = 300  # seconds

class RetryingGenerativeModel:
    def __init__(self, model_name: str, **kwargs):
        self._model = genai.GenerativeModel(model_name, **kwargs)


    async def generate_content_async(self, *args, **kwargs):
        retries = 5  # Increased from 3
        delay = 3    # Increased from 2
        
        # Add extended timeout for complex queries
        if 'request_options' not in kwargs:
            kwargs['request_options'] = RequestOptions(timeout=REQUEST_TIMEOUT)
        
        for attempt in range(retries):
            try:
                return await self._model.generate_content_async(*args, **kwargs)
            except exceptions.ResourceExhausted:
                if attempt == retries - 1:
                    raise
                wait_time = delay * (2 ** attempt)
                print(f"Rate limited, waiting {wait_time}s before retry {attempt + 1}/{retries}...")
                await asyncio.sleep(wait_time)

    def __getattr__(self, name):
        return getattr(self._model, name)


def get_model(model_name: str = "gemini-2.0-flash", **kwargs):
    # Using a fast model for planner/reviewer, can switch to pro for complex tasks
    return RetryingGenerativeModel(model_name, **kwargs)


async def get_embedding(text: str) -> list[float]:
    retries = 5  # Increased from 3
    delay = 3    # Increased from 2
    for attempt in range(retries):
        try:
            result = genai.embed_content(
                model="models/gemini-embedding-001",
                content=text,
                task_type="retrieval_query"
            )
            return result['embedding']
        except exceptions.ResourceExhausted:
            if attempt == retries - 1:
                raise
            wait_time = delay * (2 ** attempt)
            print(f"Embedding rate limited, waiting {wait_time}s before retry {attempt + 1}/{retries}...")
            await asyncio.sleep(wait_time)

