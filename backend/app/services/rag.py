"""RAG service — LangChain-based Q&A and summarization chains."""

from __future__ import annotations

import logging
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from app.config import settings
from app.services import vectorstore

logger = logging.getLogger(__name__)


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0,
        openai_api_key=settings.openai_api_key,
    )


# ── Prompt templates ──────────────────────────────────────────────────────

QA_PROMPT_TEMPLATE = """You are an intelligent document analysis assistant. Use the following context extracted from uploaded documents to answer the question. If the answer cannot be found in the context, clearly state that the information is not available in the uploaded documents.

Context:
{context}

Question: {question}

Provide a clear, detailed answer. If referencing specific parts of the documents, mention which document they come from."""

QA_PROMPT = PromptTemplate(
    template=QA_PROMPT_TEMPLATE,
    input_variables=["context", "question"],
)

SUMMARIZE_PROMPT_TEMPLATE = """You are an expert document summarizer. Provide a comprehensive yet concise summary of the following document content. Include:
1. Main topics and themes
2. Key findings or information
3. Important details and data points
4. Any conclusions or recommendations

Document content:
{text}

Summary:"""

SUMMARIZE_PROMPT = PromptTemplate(
    template=SUMMARIZE_PROMPT_TEMPLATE,
    input_variables=["text"],
)


# ── Q&A ───────────────────────────────────────────────────────────────────

def ask_question(question: str, document_ids: Optional[list[str]] = None) -> dict:
    """Run a RAG query against the FAISS index.

    Returns:
        Dict with keys: answer, sources, model.
    """
    store = vectorstore.get_store()
    if store is None:
        return {
            "answer": "No documents have been indexed yet. Please upload documents first.",
            "sources": [],
            "model": settings.openai_model,
        }

    llm = _get_llm()

    # Build retriever
    search_kwargs: dict = {"k": settings.retrieval_k}
    retriever = store.as_retriever(search_kwargs=search_kwargs)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
        chain_type_kwargs={"prompt": QA_PROMPT},
    )

    result = qa_chain.invoke({"query": question})

    # Build source list
    sources = []
    seen = set()
    for doc in result.get("source_documents", []):
        meta = doc.metadata
        key = (meta.get("document_id", ""), meta.get("chunk_index", 0))
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "content": doc.page_content[:500],
            "document_id": meta.get("document_id", ""),
            "document_name": meta.get("document_name", "Unknown"),
            "chunk_index": meta.get("chunk_index", 0),
            "relevance_score": 0.0,
        })

    # Filter sources by document_ids if specified
    if document_ids:
        sources = [s for s in sources if s["document_id"] in document_ids]

    return {
        "answer": result["result"],
        "sources": sources,
        "model": settings.openai_model,
    }


# ── Summarization ─────────────────────────────────────────────────────────

def summarize_documents(document_ids: list[str]) -> dict:
    """Generate a summary from chunks belonging to the given document IDs.

    Returns:
        Dict with keys: summary, document_ids, model.
    """
    store = vectorstore.get_store()
    if store is None:
        return {
            "summary": "No documents have been indexed yet.",
            "document_ids": document_ids,
            "model": settings.openai_model,
        }

    # Gather all chunks for the requested documents
    all_docs_dict = store.docstore._dict
    chunks: list[Document] = []
    for doc in all_docs_dict.values():
        if doc.metadata.get("document_id") in document_ids:
            chunks.append(doc)

    if not chunks:
        return {
            "summary": "No content found for the specified document(s).",
            "document_ids": document_ids,
            "model": settings.openai_model,
        }

    # Sort by chunk index for coherence
    chunks.sort(key=lambda d: d.metadata.get("chunk_index", 0))

    # Concatenate text (truncate if too long for a single call)
    combined_text = "\n\n".join(c.page_content for c in chunks)
    max_context = 12000  # rough token safety
    if len(combined_text) > max_context:
        combined_text = combined_text[:max_context] + "\n\n[Content truncated for summarization...]"

    llm = _get_llm()
    formatted_prompt = SUMMARIZE_PROMPT.format(text=combined_text)
    response = llm.invoke(formatted_prompt)

    return {
        "summary": response.content,
        "document_ids": document_ids,
        "model": settings.openai_model,
    }
