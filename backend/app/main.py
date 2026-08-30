"""FastAPI application entry point."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

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

# CORS
# allow_origins=["*"] + allow_credentials=True is rejected by browsers.
# We use wildcard for non-credentialed requests instead.
# For credentialed requests from a specific frontend, set FRONTEND_URL env var.
_frontend_url = os.getenv("FRONTEND_URL", "https://document-insight-generator-lake.vercel.app/")
_allow_origins = (
    [_frontend_url, "http://localhost:5173", "http://localhost:3000"]
    if _frontend_url
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=bool(_frontend_url),  # only True when explicit origin is set
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(summarize.router)
app.include_router(evaluation.router)


@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect bare root to the interactive API docs."""
    return RedirectResponse(url="/docs")


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
