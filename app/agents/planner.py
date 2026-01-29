import json
from app.agents.utils import get_model

class PlannerAgent:
    def __init__(self):
        self.model = get_model()

    async def plan(self, question: str) -> list[str]:
        prompt = f"""
        You are an expert financial analyst planner.
        Your goal is to decompose a complex user question about an SEC 10-K filing into a list of specific, actionable sub-questions or search queries.

        User Question: "{question}"

        Instructions:
        1. If the user asks for a calculation (e.g. "growth", "percentage difference", "margin"), you MUST create steps to find the raw numbers first.
        2. Do NOT create a step like "Calculate growth" unless you have already found the revenue numbers in previous steps.
        3. Break down the search into specific queries for each entity/year.
        4. Use variations: If searching for results for a company, create queries for synonyms:
           - Revenue: "total revenue", "net sales", "total net sales", "turnover"
           - Net Income: "net income", "net earnings", "net profit"
           - R&D: "research and development", "R&D expense", "R&D"
           - Operating Income: "operating income", "operating profit", "income from operations"


        Output a JSON object with a single key "steps" containing a list of strings.
        Example:
        {{
            "steps": [
                "Find the total revenue for 2023",
                "Find the total revenue for 2022",
                "Calculate the percentage growth"
            ]
        }}
        """
        response = await self.model.generate_content_async(prompt, generation_config={"response_mime_type": "application/json"})
        try:
            data = json.loads(response.text)
            return data.get("steps", [])
        except json.JSONDecodeError:
            return [question] # Fallback to original question
