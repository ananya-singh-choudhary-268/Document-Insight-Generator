"""Q&A query endpoint — RAG-powered question answering."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import QueryRequest, QueryResponse, SourceChunk
from app.services import rag

router = APIRouter(prefix="/api", tags=["Query"])


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """Ask a question against the indexed documents."""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key is not configured. Set OPENAI_API_KEY in the .env file.",
        )

    try:
        result = rag.ask_question(
            question=request.question,
            document_ids=request.document_ids,
        )
        return QueryResponse(
            answer=result["answer"],
            sources=[SourceChunk(**s) for s in result["sources"]],
            model=result["model"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}")
