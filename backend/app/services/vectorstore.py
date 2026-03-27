"""FAISS vector store management via LangChain."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.schema import Document

from app.config import settings

logger = logging.getLogger(__name__)

# ── Singleton index management ────────────────────────────────────────────

_faiss_store: Optional[FAISS] = None
_embeddings: Optional[OpenAIEmbeddings] = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(openai_api_key=settings.openai_api_key)
    return _embeddings


def get_store() -> Optional[FAISS]:
    """Return the current FAISS store (may be ``None`` if empty)."""
    return _faiss_store


def load_index() -> None:
    """Load persisted FAISS index from disk (if it exists)."""
    global _faiss_store
    index_path = Path(settings.faiss_index_dir)
    idx_file = index_path / "index.faiss"

    if idx_file.exists():
        try:
            _faiss_store = FAISS.load_local(
                str(index_path),
                _get_embeddings(),
                allow_dangerous_deserialization=True,
            )
            logger.info("FAISS index loaded from %s", index_path)
        except Exception as exc:
            logger.warning("Failed to load FAISS index: %s", exc)
            _faiss_store = None
    else:
        logger.info("No existing FAISS index found — starting fresh.")
        _faiss_store = None


def save_index() -> None:
    """Persist the current FAISS index to disk."""
    if _faiss_store is not None:
        _faiss_store.save_local(settings.faiss_index_dir)
        logger.info("FAISS index saved to %s", settings.faiss_index_dir)


def add_documents(chunks: list[Document]) -> int:
    """Add document chunks to the FAISS index.

    Returns:
        Number of chunks added.
    """
    global _faiss_store

    if not chunks:
        return 0

    embeddings = _get_embeddings()

    if _faiss_store is None:
        _faiss_store = FAISS.from_documents(chunks, embeddings)
    else:
        _faiss_store.add_documents(chunks)

    save_index()
    logger.info("Added %d chunks to FAISS index.", len(chunks))
    return len(chunks)


def similarity_search(
    query: str,
    k: int | None = None,
    filter_dict: dict | None = None,
) -> list[tuple[Document, float]]:
    """Search for similar chunks and return (doc, score) pairs."""
    if _faiss_store is None:
        return []
    k = k or settings.retrieval_k
    results = _faiss_store.similarity_search_with_score(query, k=k)
    return results


def delete_document(doc_id: str) -> int:
    """Remove all chunks associated with a document ID from the index.

    Returns:
        Number of chunks removed.
    """
    global _faiss_store
    if _faiss_store is None:
        return 0

    # FAISS doesn't natively support filtered deletes, so we rebuild.
    all_docs = _faiss_store.docstore._dict
    ids_to_keep = []
    docs_to_keep = []

    removed = 0
    for id_, doc in all_docs.items():
        if doc.metadata.get("document_id") == doc_id:
            removed += 1
        else:
            ids_to_keep.append(id_)
            docs_to_keep.append(doc)

    if removed == 0:
        return 0

    # Rebuild index from remaining docs
    if docs_to_keep:
        _faiss_store = FAISS.from_documents(docs_to_keep, _get_embeddings())
    else:
        _faiss_store = None

    save_index()
    logger.info("Removed %d chunks for document %s", removed, doc_id)
    return removed


def get_index_size() -> int:
    """Return the total number of vectors in the index."""
    if _faiss_store is None:
        return 0
    return _faiss_store.index.ntotal
