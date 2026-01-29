import asyncio
from app.agents.analyst import AnalystAgent

async def verify_math_tools():
    print("--- Verifying Analyst Agent with Math Tools ---")
    
    analyst = AnalystAgent()
    
    # Mock context
    context = """
    Apple 2022 Revenue: $394,328 million
    Apple 2023 Revenue: $383,285 million
    Apple 2023 Cost of Sales: $214,136 million
    """
    
    question = "Calculate Apple's revenue growth from 2022 to 2023 and the 2023 gross margin."
    
    print(f"Question: {question}")
    print("Generating answer (expecting tool usage)...")
    
    answer = await analyst.analyze(question, context)
    
    print("\n--- Answer ---")
    print(answer)
    
    if "2.8%" in answer or "-2.8" in answer or "44.1" in answer:
        print("\nSUCCESS: Answer contains calculated numbers.")
    else:
        print("\nWARN: Answer might not be using tools correctly. Check numbers.")

if __name__ == "__main__":
    # Ensure env vars are loaded for Gemini Key
    from dotenv import load_dotenv
    load_dotenv()
    
    asyncio.run(verify_math_tools())
