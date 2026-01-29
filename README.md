# SEC Agent RAG

An intelligent, agentic RAG pipeline for analyzing SEC 10-K filings using **Gemini** and **PostgreSQL + pgvector**.

## ✨ Key Features

| Feature | Description |
| :--- | :--- |
| **Auto-Ingestion** | Ask about any company—filings are downloaded from SEC EDGAR automatically |
| **Multi-Company Comparison** | Compare metrics across multiple companies (e.g., "Compare Apple and Microsoft revenue") |
| **Year Precision** | Parses SEC headers to ensure correct fiscal year data |
| **Financial Data Boost** | Prioritizes chunks with actual financial data (`$`, income statements) |
| **Hybrid Search** | Combines vector search + keyword search with RRF ranking |
| **Flutter Chat UI** | Modern web interface for financial Q&A |

## 🚀 Quick Start

### Prerequisites
- Docker Desktop (running)
- Python 3.11+
- Flutter SDK (for frontend)

### 1. Start Services
```bash
docker compose up -d
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. (Optional) Bulk Ingest Companies
Pre-load data for faster queries:
```bash
python bulk_ingest.py AAPL,MSFT,GOOGL,AMZN,META,TSLA --year 2023
```

### 3. Ask Questions
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{"user_input": "What was Apple revenue in 2023?"}'
```

### 4. Run the Chat UI
```bash
cd frontend
flutter run -d web-server --web-port 3000
```
Open **[http://127.0.0.1:3000](http://127.0.0.1:3000)**

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Flutter UI  │────▶│  FastAPI     │────▶│  PostgreSQL  │
│  (Port 3000) │     │  (Port 8000) │     │  + pgvector  │
└──────────────┘     └──────────────┘     └──────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Planner  │  │  Search  │  │ Reviewer │
        │  Agent   │  │  Agent   │  │  Agent   │
        └──────────┘  └──────────┘  └──────────┘
              │             │             │
              └─────────────┴─────────────┘
                            │
                    ┌───────▼───────┐
                    │    Gemini     │
                    │   (LLM API)   │
                    └───────────────┘
```

### Agents
- **ClassifierAgent**: Extracts tickers and years from natural language
- **PlannerAgent**: Breaks complex questions into sub-queries
- **SearchAgent**: Hybrid search with financial data boosting
- **AnalystAgent**: Synthesizes answers from retrieved context
- **ReviewerAgent**: Validates answers against source data

## 📊 Verified Companies

| Company | Ticker | 2023 Data |
| :--- | :--- | :--- |
| Apple | AAPL | ✅ $383,285M revenue |
| Microsoft | MSFT | ✅ $211,915M revenue |
| Meta | META | ✅ $39,098M net income |
| Tesla | TSLA | ✅ $3,969M R&D |
| Amazon | AMZN | ✅ $30,425M net income |
| Google | GOOGL | ✅ $73,795M net income |

## 🔧 Environment Variables

Create a `.env` file:
```env
GEMINI_API_KEY=your-api-key
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/sec_rag
SEC_COMPANY=YourCompany
SEC_EMAIL=your@email.com
```

## 📁 Project Structure

```
sec-agent-rag/
├── app/
│   ├── agents/          # AI agents (planner, search, reviewer, etc.)
│   ├── api/             # FastAPI endpoints
│   ├── services/        # SEC download & ingestion
│   └── models.py        # SQLAlchemy models
├── frontend/            # Flutter chat UI
├── sec_downloads/       # Cached SEC filings
├── bulk_ingest.py       # CLI for batch ingestion
└── docker-compose.yml   # PostgreSQL + pgvector
```

## 🐛 Troubleshooting

| Issue | Solution |
| :--- | :--- |
| "Address already in use" | Server is already running |
| "No data found" | Run `python bulk_ingest.py TICKER --year YEAR` |
| Docker not running | Start Docker Desktop |

## License

MIT
