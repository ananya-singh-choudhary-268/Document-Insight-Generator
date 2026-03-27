"""Pydantic request/response models for the API."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Documents ──────────────────────────────────────────────────────────────

class DocumentResponse(BaseModel):
    """Metadata for a single uploaded document."""

    id: str
    filename: str
    file_type: str
    file_size: int  # bytes
    page_count: int = 0
    chunk_count: int = 0
    language: str = "eng"
    status: str = "processing"  # processing | ready | error
    uploaded_at: str = ""
    error_message: Optional[str] = None


class DocumentListResponse(BaseModel):
    """Wrapper for listing all documents."""

    documents: list[DocumentResponse]
    total: int


# ── Query (Q&A) ───────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    """User question sent to the RAG pipeline."""

    question: str = Field(..., min_length=1, max_length=2000)
    document_ids: Optional[list[str]] = None  # scope to specific docs


class SourceChunk(BaseModel):
    """A retrieved source chunk returned alongside the answer."""

    content: str
    document_id: str
    document_name: str
    chunk_index: int = 0
    relevance_score: float = 0.0


class QueryResponse(BaseModel):
    """Answer returned by the RAG pipeline."""

    answer: str
    sources: list[SourceChunk] = []
    model: str = ""


# ── Summarization ─────────────────────────────────────────────────────────

class SummaryRequest(BaseModel):
    """Request to summarize one or more documents."""

    document_ids: list[str] = Field(..., min_length=1)


class SummaryResponse(BaseModel):
    """Generated summary."""

    summary: str
    document_ids: list[str]
    model: str = ""


# ── Health ─────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    document_count: int = 0
    index_size: int = 0
    tesseract_available: bool = False
    openai_configured: bool = False
