import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("POSTGRES_USER", "user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "sec_filings")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5432/{POSTGRES_DB}"

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def init_db():
    async with engine.begin() as conn:
        # Enable pgvector extension
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        
        # Manually add search_vector column if it doesn't exist (migrations are better but this works for MVP)
        await conn.execute(text(
            "ALTER TABLE filings ADD COLUMN IF NOT EXISTS search_vector tsvector"
        ))
        
        # Backfill search_vector for existing rows
        await conn.execute(text(
            "UPDATE filings SET search_vector = to_tsvector('english', text_content) WHERE search_vector IS NULL"
        ))

        
        # Add GIN index for full text search
        # We use strict SQL execution to ensure it exists
        await conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_filings_search_vector ON filings USING GIN (search_vector)"
        ))
        
        # Add trigger to auto-update search_vector from text_content
        # Postgres requires a function and a trigger
        await conn.execute(text("""
            CREATE OR REPLACE FUNCTION filings_search_vector_update() RETURNS trigger AS $$
            BEGIN
                NEW.search_vector := to_tsvector('english', NEW.text_content);
                RETURN NEW;
            END
            $$ LANGUAGE plpgsql;
        """))
        
        await conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'tsvectorupdate') THEN
                    CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE
                    ON filings FOR EACH ROW EXECUTE FUNCTION filings_search_vector_update();
                END IF;
            END
            $$;
        """))


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
