"""Summarization endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import SummaryRequest, SummaryResponse
from app.services import rag

router = APIRouter(prefix="/api", tags=["Summarize"])


@router.post("/summarize", response_model=SummaryResponse)
async def summarize_documents(request: SummaryRequest):
    """Generate a summary for the given document(s)."""
    if not settings.openai_api_key:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key is not configured. Set OPENAI_API_KEY in the .env file.",
        )

    try:
        result = rag.summarize_documents(document_ids=request.document_ids)
        return SummaryResponse(
            summary=result["summary"],
            document_ids=result["document_ids"],
            model=result["model"],
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {exc}")
