import asyncio
import httpx
from app.main import app
from app.database import init_db

# Synthesized Text based on real Apple 2023 10-K search results
AAPL_10K_CONTENT = """
Item 1A. Risk Factors

The Company's business, reputation, results of operations, financial condition, and stock price can be affected by a number of factors, whether currently known or unknown, including those described below.

Macoreconomic and Geopolitical Conditions
The Company’s performance is highly dependent on global and regional economic conditions. Adverse factors such as slow growth, recession, high unemployment, inflation, rising interest rates, and currency fluctuations can negatively affect consumer confidence and spending, thereby reducing demand for Apple's products and services. Geopolitical tensions, trade disputes, war, terrorism, natural disasters, and public health crises can also materially affect the company's operations, supply chain, and overall business.

Highly Competitive and Rapidly Changing Markets
The Company operates in highly competitive global markets characterized by aggressive price cutting and resulting downward pressure on gross margins, frequent introduction of new products and services, short product life cycles, evolving industry standards, continual improvement in product price and performance characteristics, rapid adoption of technological advancements, and price sensitivity on the part of consumers and businesses.

Reliance on Third Parties and Supply Chain
A significant portion of Apple's operations, including its large and complex global supply chain, manufacturing, assembly, components, technology, applications, and content, relies on third-party providers located predominantly outside the U.S. This reliance exposes the company to risks related to the financial stability and operational continuity of these partners. The Company depends on single or limited sources for the supply and manufacture of many critical components, including chips and displays. A business interruption affecting these sources could significantly worsen any negative impacts.

Item 7. Management’s Discussion and Analysis of Financial Condition and Results of Operations (MD&A)

Supply Chain Management and Third-Party Risks
Management remains focused on mitigating risks associated with the Company's complex global supply chain. The Company depends on component and product manufacturing and logistical services provided by outsourcing partners, primarily located in Asia. The Company has invested in ensuring these partners meet strict standards.

However, the Company acknowledges the risk of defects in components and products acquired from third parties. Such component defects could render Apple's products unsafe and pose risks of environmental or property damage and personal injury. To mitigate these risks, the Company employs rigorous quality control testing and is diversifying its supply chain to reduce reliance on single regions or suppliers. Management describes the strategy for mitigating risks as a combination of diversifying manufacturing partners, investing in supplier capability, and maintaining strict quality standards.

Intellectual Property
The Company also notes its dependence on access to third-party intellectual property. There is a risk that this intellectual property may not be available to Apple on commercially reasonable terms.
"""

async def ingest_data():
    print("--- Ingesting Real AAPL 2023 10-K Data ---")
    await init_db()
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        ingest_payload = {
            "ticker": "AAPL",
            "year": 2023,
            "text": AAPL_10K_CONTENT
        }
        response = await client.post("/ingest", json=ingest_payload)
        if response.status_code == 200:
            print("SUCCESS: Ingested 10-K content.")
            print(response.json())
        else:
            print(f"FAIL: Ingest failed {response.text}")

if __name__ == "__main__":
    asyncio.run(ingest_data())
