from app.agents.utils import get_model

class ReviewerAgent:
    def __init__(self):
        self.model = get_model()

    async def review(self, question: str, answer: str, context: list[str]) -> str:
        context_text = "\n\n".join(context)
        prompt = f"""
        You are a Senior Financial Analyst and strict compliance reviewer.
        Your job is to verify that the generated answer is directly supported by the provided context from SEC 10-K filings.

        Question: {question}
        Proposed Answer: {answer}

        Context:
        {context_text}

        Instructions:
        1. MANDATORY: The **very first sentence** of your response MUST explicitly state the full company name and the fiscal year being discussed (e.g., "For Apple Inc. in fiscal year 2023...").
        2. STRICT NEGATIVE CONSTRAINT: DO NOT use preambles like "Based on the filing", "According to the context", or "Analyzing the data". Start immediately with the fact.
        3. Check if all numbers in the answer appear in the Context.
        4. Recognize synonyms: "Revenue" is the same as "Net Sales" or "Total Sales".
        5. If the answer is correct and supported, return it as is (subject to the formatting rules above).
        6. If there are discrepancies, correct the answer to ONLY state what is in the Context.
        7. If the context does not contain the answer, state that the information is not found in the provided text.

        Return ONLY the final corrected answer.
        """
        response = await self.model.generate_content_async(prompt)
        return response.text.strip()

    async def stream_review(self, question: str, answer: str, context: list[str]):
        """Streaming version of review"""
        # Yielding status is now handled by the API endpoint as a separate event type.
        # We start streaming the actual text immediately.
        
        context_text = "\n\n".join(context)
        prompt = f"""
        You are a Senior Financial Analyst and strict compliance reviewer.
        Your job is to verify that the generated answer is directly supported by the provided context from SEC 10-K filings.

        Question: {question}
        Proposed Answer: {answer}

        Context:
        {context_text}

        Instructions:
        1. MANDATORY: The **very first sentence** of your response MUST explicitly state the full company name and the fiscal year being discussed (e.g., "For Apple Inc. in fiscal year 2023...").
        2. STRICT NEGATIVE CONSTRAINT: DO NOT use preambles like "Based on the filing", "According to the context", or "Analyzing the data". Start immediately with the fact.
        3. Check if all numbers in the answer appear in the Context.
        4. Recognize synonyms: "Revenue" is the same as "Net Sales".
        5. If the answer is correct, return it as is (subject to the formatting rules above).
        6. If there are discrepancies, correct the answer to ONLY state what is in the Context.
        7. Return ONLY the final corrected answer.
        """
        async for chunk in self.model.generate_content_stream_async(prompt):
            if chunk.text:
                yield chunk.text
