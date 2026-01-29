import json
from datetime import datetime
from app.agents.utils import get_model

class ClassifierAgent:
    def __init__(self):
        self.model = get_model("gemini-2.0-flash")

    async def classify(self, user_input: str) -> dict:
        import asyncio
        from google.api_core import exceptions
        
        current_year = datetime.now().year
        prompt = f"""
        You are a financial query parser.
        Your job is to extract the Stock Ticker(s) (e.g., AAPL, GOOGL) and the Fiscal Year from the user's question.
        If the user mentions multiple companies for comparison, extract ALL of them.

        User Question: "{user_input}"

        Instructions:
        1. Identify the company/companies and convert them to stock ticker symbols (e.g., Apple -> AAPL, Microsoft -> MSFT).
        2. Identify the year. If no year is mentioned, use {current_year - 1} (last completed fiscal year).
        3. Return ONLY a JSON object with keys "tickers" (a list of strings) and "year".

        Example Output for "Compare Apple and Microsoft":
        {{
            "tickers": ["AAPL", "MSFT"],
            "year": 2023
        }}

        """
        
        retries = 3
        delay = 2
        for attempt in range(retries):
            try:
                response = await self.model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
                break
            except exceptions.ResourceExhausted:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(delay * (2 ** attempt))

        try:
            data = json.loads(response.text)
            # Ensure return format is consistent (list of tickers)
            if "ticker" in data and "tickers" not in data:
                data["tickers"] = [data["ticker"]]
            if "tickers" not in data:
                data["tickers"] = ["UNKNOWN"]
            return data
        except json.JSONDecodeError:
            # Fallback default if parsing fails
            return {"tickers": ["UNKNOWN"], "year": current_year - 1}

