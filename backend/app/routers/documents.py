"""Document management endpoints — upload, list, get, delete."""

from __future__ import annotations

import shutil
import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import Optional

from app.config import settings
from app.models import DocumentResponse, DocumentListResponse
from app.services import document_processor, ocr

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["Documents"])


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Upload a document for OCR processing and indexing."""
    # Validate file extension
    ext = Path(file.filename or "unknown").suffix.lower()
    if ext not in ocr.SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(sorted(ocr.SUPPORTED_EXTENSIONS))}",
        )

    # Save uploaded file
    doc_id_prefix = ""  # will be set by processor
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Use a temp name; the processor will assign an ID
    import uuid
    temp_name = f"tmp_{uuid.uuid4().hex[:8]}{ext}"
    file_path = upload_dir / temp_name

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Process (extract text → chunk → index)
        meta = document_processor.process_document(
            file_path,
            original_filename=file.filename or "unknown",
            lang=language,
        )

        # Rename file to include document ID
        final_name = f"{meta['id']}_{file.filename}"
        final_path = upload_dir / final_name
        file_path.rename(final_path)

        return DocumentResponse(**meta)

    except Exception as exc:
        # Clean up temp file on failure
        if file_path.exists():
            file_path.unlink()
        logger.exception("Upload failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents."""
    docs = document_processor.get_all_documents()
    return DocumentListResponse(
        documents=[DocumentResponse(**d) for d in docs],
        total=len(docs),
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(doc_id: str):
    """Get metadata for a single document."""
    meta = document_processor.get_document(doc_id)
    if meta is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse(**meta)


@router.delete("/{doc_id}")
async def delete_document(doc_id: str):
    """Delete a document and remove it from the index."""
    success = document_processor.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully", "id": doc_id}
