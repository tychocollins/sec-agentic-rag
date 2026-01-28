from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown

from app.api.endpoints import router
app = FastAPI(title="SEC Agent RAG", lifespan=lifespan)
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "SEC Agent RAG API is running"}
