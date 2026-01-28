import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)

def get_model(model_name: str = "gemini-3-flash-preview"):
    # Using a fast model for planner/reviewer, can switch to pro for complex tasks
    return genai.GenerativeModel(model_name)

async def get_embedding(text: str) -> list[float]:
    result = genai.embed_content(
        model="models/gemini-embedding-001",
        content=text,
        task_type="retrieval_query"
    )
    return result['embedding']
