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
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from google.api_core import exceptions

from fastapi import Request
import time

app = FastAPI(title="SEC Agent RAG", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)




app.include_router(router)

@app.get("/")
async def root():
    return {"message": "SEC Agent RAG API is running"}

@app.exception_handler(exceptions.ResourceExhausted)
async def resource_exhausted_exception_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={"message": "Service is busy (Quota Exceeded). Please try again later."},
        headers={"Access-Control-Allow-Origin": request.headers.get("origin") or "*"}
    )

