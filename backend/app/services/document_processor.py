"""Document processor — orchestrates text extraction, chunking, and indexing."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.config import settings
from app.services import ocr, vectorstore

logger = logging.getLogger(__name__)

# ── In-memory document metadata registry ──────────────────────────────────
# In production you'd use a database; here we persist a simple JSON file.

_METADATA_FILE = Path(settings.upload_dir) / "_metadata.json"
_documents: dict[str, dict] = {}


def _load_metadata() -> None:
    global _documents
    if _METADATA_FILE.exists():
        with open(_METADATA_FILE, "r") as f:
            _documents = json.load(f)
    else:
        _documents = {}


def _save_metadata() -> None:
    _METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(_METADATA_FILE, "w") as f:
        json.dump(_documents, f, indent=2, default=str)


def init() -> None:
    """Load persisted metadata on startup."""
    _load_metadata()
    logger.info("Loaded metadata for %d documents.", len(_documents))


# ── Public API ────────────────────────────────────────────────────────────


def get_all_documents() -> list[dict]:
    """Return metadata for every uploaded document."""
    return list(_documents.values())


def get_document(doc_id: str) -> dict | None:
    return _documents.get(doc_id)


def process_document(file_path: str | Path, original_filename: str, lang: str | None = None) -> dict:
    """Full ingestion pipeline: extract text → chunk → embed → store.

    Returns:
        Document metadata dict.
    """
    doc_id = uuid.uuid4().hex[:12]
    path = Path(file_path)

    meta: dict = {
        "id": doc_id,
        "filename": original_filename,
        "file_type": path.suffix.lower().lstrip("."),
        "file_size": path.stat().st_size,
        "page_count": 0,
        "chunk_count": 0,
        "language": lang or settings.tesseract_lang,
        "status": "processing",
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "error_message": None,
    }

    try:
        # 1. Extract text
        text, page_count = ocr.extract_text(path, lang)
        meta["page_count"] = page_count

        if not text.strip():
            meta["status"] = "error"
            meta["error_message"] = "No text could be extracted from the document."
            _documents[doc_id] = meta
            _save_metadata()
            return meta

        # 2. Chunk
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
        )
        chunks_text = splitter.split_text(text)
        chunks = [
            Document(
                page_content=chunk,
                metadata={
                    "document_id": doc_id,
                    "document_name": original_filename,
                    "chunk_index": i,
                },
            )
            for i, chunk in enumerate(chunks_text)
        ]

        meta["chunk_count"] = len(chunks)

        # 3. Index — try to embed and store in FAISS
        try:
            vectorstore.add_documents(chunks)
            meta["status"] = "ready"
        except Exception as embed_exc:
            # Embedding failed (e.g. invalid API key) but text was extracted.
            # Mark as ready so the document is visible, but note the issue.
            logger.warning(
                "Embedding failed for %s: %s. Document text extracted but not indexed.",
                original_filename, embed_exc,
            )
            meta["status"] = "ready"
            meta["error_message"] = f"Text extracted but indexing failed: {embed_exc}"

    except Exception as exc:
        logger.exception("Error processing document %s", original_filename)
        meta["status"] = "error"
        meta["error_message"] = str(exc)

    _documents[doc_id] = meta
    _save_metadata()
    return meta


def delete_document(doc_id: str) -> bool:
    """Delete a document's file, chunks, and metadata."""
    meta = _documents.get(doc_id)
    if meta is None:
        return False

    # Remove from vector store
    vectorstore.delete_document(doc_id)

    # Remove file
    file_path = Path(settings.upload_dir) / f"{doc_id}_{meta['filename']}"
    if file_path.exists():
        file_path.unlink()

    # Remove metadata
    del _documents[doc_id]
    _save_metadata()
    logger.info("Deleted document %s (%s)", doc_id, meta["filename"])
    return True


def get_document_count() -> int:
    return len(_documents)
