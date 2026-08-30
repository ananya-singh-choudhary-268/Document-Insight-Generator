"""FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models import HealthResponse
from app.services import document_processor, vectorstore, ocr
from app.routers import documents, query, summarize, evaluation

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s │ %(levelname)-8s │ %(name)s │ %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown events."""
    logger.info("🚀  Starting Document Insight Generator backend …")
    vectorstore.load_index()
    document_processor.init()
    idx_size = vectorstore.get_index_size()
    doc_count = document_processor.get_document_count()
    logger.info("   📄  %d documents, %d vectors in index", doc_count, idx_size)
    yield
    logger.info("👋  Shutting down …")


app = FastAPI(
    title="Smart Document Insight Generator",
    description="GenAI RAG platform for extracting insights from semi-structured documents using OCR, FAISS, and LangChain.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(summarize.router)
app.include_router(evaluation.router)


@app.get("/api/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint with system status."""
    return HealthResponse(
        status="ok",
        document_count=document_processor.get_document_count(),
        index_size=vectorstore.get_index_size(),
        tesseract_available=ocr.is_tesseract_available(),
        openai_configured=bool(settings.openai_api_key),
    )
