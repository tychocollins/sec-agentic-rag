from sqlalchemy import Column, Integer, String, Text, Computed
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector
from app.database import Base


class Filing(Base):
    __tablename__ = "filings"

    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String, index=True)
    year = Column(Integer, index=True)
    chunk_index = Column(Integer)
    text_content = Column(Text)
    # Using 3072 dimensions for Gemini embeddings (embedding-001)
    # Adjust dimension if using a different model
    embedding = Column(Vector(3072))
    
    # Full text search vector
    # 'english' configuration is standard
    search_vector = Column(TSVECTOR)


    def __repr__(self):
        return f"<Filing(ticker={self.ticker}, year={self.year}, chunk={self.chunk_index})>"
