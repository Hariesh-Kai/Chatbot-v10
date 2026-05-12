from __future__ import annotations

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    document_id: str = Field(..., description="Unique document id")
    file_path: str = Field(..., description="Local path for reference implementation")


class IngestResponse(BaseModel):
    document_id: str
    chunks_indexed: int


class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    document_id: str | None = None
    section: str | None = None


class CitationResponse(BaseModel):
    document_id: str
    chunk_id: str
    page_start: int | None
    page_end: int | None
    section: str | None


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    citations: list[CitationResponse]
