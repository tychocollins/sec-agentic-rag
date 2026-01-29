# SEC Agent RAG

An Agentic RAG pipeline for analyzing SEC 10-K filings using **Gemini 3** and **Postgres via pgvector**.

## Status
The server is likely **already running** on your machine (Port 8000).

## Usage

### 1. Ingest Data
Before analyzing, you need to load data into the database.
```bash
curl -X POST "http://localhost:8000/ingest" \
     -H "Content-Type: application/json" \
     -d '{
           "ticker": "AAPL",
           "year": 2023,
           "text": "Apple Inc. reported total net sales of $383,285 million for 2023."
         }'
```

### 2. Analyze (Ask a Question)
The **Planner Agent** will break down your question, the **Search Agent** will find data, and the **Reviewer Agent** will verify the answer.
```bash
curl -X POST "http://localhost:8000/analyze" \
     -H "Content-Type: application/json" \
     -d '{
           "ticker": "AAPL",
           "year": 2023,
           "question": "What was the total net sales?"
         }'
```

### 3. Interactive UI
Open your browser to **[http://localhost:8000/docs](http://localhost:8000/docs)** to use the generic Swagger UI.

## Troubleshooting
- **"Address already in use"**: This means the server is already running! You don't need to start it again.
- **Docker**: Ensure Docker Desktop is running (`docker compose up -d`).

## Running the Web App (Frontend)

To start the chat interface with a fixed URL:

1.  Navigate to the frontend folder:
    ```bash
    cd frontend
    ```
2.  Run Flutter Web Server (Stable):
    ```bash
    flutter run -d web-server --web-port 3000
    ```
3.  Open your browser to: **[http://127.0.0.1:3000](http://127.0.0.1:3000)**
