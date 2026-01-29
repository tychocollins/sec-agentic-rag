from app.agents.utils import get_model

class ReviewerAgent:
    def __init__(self):
        self.model = get_model()

    async def review(self, question: str, answer: str, context: list[str]) -> str:
        context_text = "\n\n".join(context)
        prompt = f"""
        You are a strict compliance reviewer for financial data.
        Your job is to verify that the generated answer is directly supported by the provided context from SEC 10-K filings.

        Question: {question}
        Proposed Answer: {answer}

        Context:
        {context_text}

        Instructions:
        1. Check if all numbers (revenue, EPS, dates, etc.) in the answer appear in the Context.
        2. Recognize synonyms: "Revenue" is the same as "Net Sales" or "Total Sales".
        3. Calculations: If the answer uses a tool-derived calculation (like growth %), verify that the *raw numbers* used for the calculation are in the context.
        4. If the answer is correct and supported, return it as is.
        5. If there are discrepancies or unsupported claims, correct the answer to ONLY state what is in the Context.
        6. If the context does not contain the answer, state that the information is not found in the provided text.


        Return ONLY the final corrected answer.
        """
        response = await self.model.generate_content_async(prompt)
        return response.text.strip()

    async def stream_review(self, question: str, answer: str, context: list[str]):
        """Streaming version of review"""
        context_text = "\n\n".join(context)
        prompt = f"""
        You are a strict compliance reviewer for financial data.
        Your job is to verify that the generated answer is directly supported by the provided context from SEC 10-K filings.

        Question: {question}
        Proposed Answer: {answer}

        Context:
        {context_text}

        Instructions:
        1. Check if all numbers in the answer appear in the Context.
        2. Recognize synonyms: "Revenue" is the same as "Net Sales".
        3. If the answer is correct, return it as is.
        4. If there are discrepancies, correct the answer to ONLY state what is in the Context.
        5. Return ONLY the final corrected answer.
        """
        async for chunk in self.model.generate_content_stream_async(prompt):
            if chunk.text:
                yield chunk.text
