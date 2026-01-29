from app.agents.utils import get_model
from app.tools.calculator import FinancialTools
import google.generativeai as genai

class AnalystAgent:
    def __init__(self):
        # We initialize the model with the tools
        self.tools = FinancialTools()
        # Create a list of callables for the model tools
        self.model_tools = [
            self.tools.percentage_change,
            self.tools.margin,
            self.tools.ratio
        ]
        # Initialize model with tools
        self.model = get_model(tools=self.model_tools)

    async def analyze(self, question: str, context: str) -> str:
        """
        Analyzes the question given the context, potentially using calculator tools.
        """
        prompt = f"""
        You are an expert financial analyst.
        Answer the user's question based ONLY on the provided context.
        
        Terminology Note: "Revenue", "Net Sales", "Total Sales", and "Turnover" are often used interchangeably in these filings. Treat them as the same metric unless specifically noted otherwise.
        
        If you need to perform calculations (growth, margins, ratios), USE THE PROVIDED TOOLS.
        Do not try to calculate numbers in your head.

        
        User Question: {question}
        
        Context:
        {context}
        """
        
        # We need automatic function calling handling
        # Gemini Python SDK handles this with automatic_function_calling=True usually,
        # or we manually handle the history.
        # For simplicity in this async env, we'll let the chat session handle it.
        
        from google.api_core import exceptions
        import asyncio
        
        retries = 3
        delay = 2
        
        for attempt in range(retries):
            try:
                chat = self.model.start_chat(enable_automatic_function_calling=True)
                response = await chat.send_message_async(prompt)
                return response.text
            except exceptions.ResourceExhausted:
                if attempt == retries - 1:
                    raise
                await asyncio.sleep(delay * (2 ** attempt))
            except Exception as e:
                # Other errors should propagate but we can log them
                raise e

