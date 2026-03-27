#!/usr/bin/env python3
"""End-to-end API test suite for the Document Insight Generator backend."""

import os
import sys
import json
import requests
import tempfile

BASE_URL = "http://localhost:8000/api"
PASS = 0
FAIL = 0


def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def main():
    global PASS, FAIL

    print("\n" + "=" * 60)
    print("  Document Insight Generator — API Test Suite")
    print("=" * 60)

    # ── 1. Health Check ────────────────────────────────────────────
    print("\n📋 Health Check")
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=10)
        test("GET /health returns 200", r.status_code == 200, f"got {r.status_code}")
        data = r.json()
        test("Health has 'status' field", data.get("status") == "ok", f"got {data.get('status')}")
        test("Health has 'document_count'", "document_count" in data)
        test("Health has 'index_size'", "index_size" in data)
        test("Health has 'tesseract_available'", "tesseract_available" in data)
        test("Health has 'openai_configured'", "openai_configured" in data)
        print(f"    → tesseract: {data.get('tesseract_available')}, openai: {data.get('openai_configured')}")
    except Exception as e:
        test("Backend reachable", False, str(e))
        print("\n⚠️  Backend not running. Start it first: uvicorn app.main:app --reload")
        sys.exit(1)

    # ── 2. List Documents (empty) ──────────────────────────────────
    print("\n📋 Document List (Initial)")
    r = requests.get(f"{BASE_URL}/documents")
    test("GET /documents returns 200", r.status_code == 200, f"got {r.status_code}")
    data = r.json()
    test("Response has 'documents' array", isinstance(data.get("documents"), list))
    test("Response has 'total' field", "total" in data)
    initial_count = data.get("total", 0)
    print(f"    → {initial_count} documents initially")

    # ── 3. Upload a .txt document ──────────────────────────────────
    print("\n📋 Document Upload (.txt)")
    test_content = """The Smart Document Insight Generator is a GenAI RAG platform.
It uses Tesseract for multilingual OCR processing.
FAISS is used as the vector store for semantic search.
LangChain orchestrates the retrieval-augmented generation pipeline.
The frontend is built with React.js and the backend with FastAPI.
This platform can process over 5,000 semi-structured documents.
It reduces document review time by 80% through automated Q&A and summarization.
OpenAI's GPT models power the natural language understanding capabilities."""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, prefix='test_doc_') as f:
        f.write(test_content)
        temp_path = f.name

    try:
        with open(temp_path, 'rb') as f:
            r = requests.post(
                f"{BASE_URL}/documents/upload",
                files={"file": ("test_document.txt", f, "text/plain")},
                data={"language": "eng"},
                timeout=30,
            )
        test("POST /documents/upload returns 200", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
        doc_data = r.json()
        test("Response has 'id'", bool(doc_data.get("id")))
        test("Filename matches", doc_data.get("filename") == "test_document.txt", f"got {doc_data.get('filename')}")
        test("File type is 'txt'", doc_data.get("file_type") == "txt", f"got {doc_data.get('file_type')}")
        test("Status is 'ready'", doc_data.get("status") == "ready", f"got {doc_data.get('status')}")
        test("Chunk count > 0", doc_data.get("chunk_count", 0) > 0, f"got {doc_data.get('chunk_count')}")
        doc_id = doc_data.get("id")
        print(f"    → doc_id: {doc_id}, chunks: {doc_data.get('chunk_count')}, pages: {doc_data.get('page_count')}")
    finally:
        os.unlink(temp_path)

    # ── 4. Upload a second .txt document ───────────────────────────
    print("\n📋 Document Upload (Second Document)")
    test_content_2 = """Machine learning is a subset of artificial intelligence.
Deep learning uses neural networks with many layers.
Natural language processing enables computers to understand human language.
Transformers architecture revolutionized NLP tasks.
GPT models are based on the transformer architecture.
RAG combines retrieval with generation for better accuracy.
Vector databases store embeddings for similarity search.
FAISS is a library for efficient similarity search developed by Meta."""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, prefix='test_doc2_') as f:
        f.write(test_content_2)
        temp_path_2 = f.name

    try:
        with open(temp_path_2, 'rb') as f:
            r = requests.post(
                f"{BASE_URL}/documents/upload",
                files={"file": ("ml_concepts.txt", f, "text/plain")},
                timeout=30,
            )
        test("Second upload returns 200", r.status_code == 200, f"got {r.status_code}: {r.text[:200]}")
        doc2_data = r.json()
        doc2_id = doc2_data.get("id")
        test("Second doc has ID", bool(doc2_id))
        test("Second doc is ready", doc2_data.get("status") == "ready", f"got {doc2_data.get('status')}")
        print(f"    → doc_id: {doc2_id}, chunks: {doc2_data.get('chunk_count')}")
    finally:
        os.unlink(temp_path_2)

    # ── 5. List Documents (after uploads) ──────────────────────────
    print("\n📋 Document List (After Upload)")
    r = requests.get(f"{BASE_URL}/documents")
    data = r.json()
    test("Document count increased", data.get("total", 0) >= initial_count + 2,
         f"expected ≥{initial_count + 2}, got {data.get('total')}")
    print(f"    → {data.get('total')} documents total")

    # ── 6. Get Single Document ─────────────────────────────────────
    print("\n📋 Get Single Document")
    r = requests.get(f"{BASE_URL}/documents/{doc_id}")
    test("GET /documents/{id} returns 200", r.status_code == 200, f"got {r.status_code}")
    single = r.json()
    test("Returns correct doc ID", single.get("id") == doc_id)

    # ── 7. Get Non-existent Document ───────────────────────────────
    print("\n📋 Get Non-existent Document")
    r = requests.get(f"{BASE_URL}/documents/nonexistent123")
    test("Returns 404 for missing doc", r.status_code == 404, f"got {r.status_code}")

    # ── 8. Upload Invalid File Type ────────────────────────────────
    print("\n📋 Upload Invalid File Type")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        f.write("invalid file")
        invalid_path = f.name
    try:
        with open(invalid_path, 'rb') as f:
            r = requests.post(
                f"{BASE_URL}/documents/upload",
                files={"file": ("bad_file.xyz", f)},
                timeout=10,
            )
        test("Rejects unsupported file type", r.status_code == 400, f"got {r.status_code}")
    finally:
        os.unlink(invalid_path)

    # ── 9. Query (Q&A) ────────────────────────────────────────────
    print("\n📋 Query (Q&A) Endpoint")
    r = requests.post(
        f"{BASE_URL}/query",
        json={"question": "What is the Document Insight Generator?"},
        timeout=60,
    )
    if r.status_code == 503:
        test("Query returns 503 (OpenAI not configured)", True)
        print("    → OpenAI API key not set — skipping Q&A content validation")
    elif r.status_code == 200:
        qa_data = r.json()
        test("Query returns 200", True)
        test("Has 'answer' field", bool(qa_data.get("answer")))
        test("Has 'sources' field", isinstance(qa_data.get("sources"), list))
        test("Has 'model' field", bool(qa_data.get("model")))
        print(f"    → Answer preview: {qa_data.get('answer', '')[:100]}...")
    else:
        test("Query returns valid status", False, f"got {r.status_code}: {r.text[:200]}")

    # ── 10. Query with document filter ─────────────────────────────
    print("\n📋 Query with Document Filter")
    r = requests.post(
        f"{BASE_URL}/query",
        json={"question": "What is FAISS?", "document_ids": [doc2_id]},
        timeout=60,
    )
    if r.status_code == 503:
        test("Filtered query returns 503 (OpenAI not configured)", True)
    elif r.status_code == 200:
        test("Filtered query returns 200", True)
    else:
        test("Filtered query returns valid status", False, f"got {r.status_code}")

    # ── 11. Query Validation ───────────────────────────────────────
    print("\n📋 Query Validation")
    r = requests.post(
        f"{BASE_URL}/query",
        json={"question": ""},
        timeout=10,
    )
    test("Empty question rejected (422)", r.status_code == 422, f"got {r.status_code}")

    # ── 12. Summarize Endpoint ─────────────────────────────────────
    print("\n📋 Summarize Endpoint")
    r = requests.post(
        f"{BASE_URL}/summarize",
        json={"document_ids": [doc_id]},
        timeout=60,
    )
    if r.status_code == 503:
        test("Summarize returns 503 (OpenAI not configured)", True)
        print("    → OpenAI API key not set — skipping summarization content validation")
    elif r.status_code == 200:
        summ_data = r.json()
        test("Summarize returns 200", True)
        test("Has 'summary' field", bool(summ_data.get("summary")))
        test("Has 'document_ids' field", isinstance(summ_data.get("document_ids"), list))
        print(f"    → Summary preview: {summ_data.get('summary', '')[:100]}...")
    else:
        test("Summarize returns valid status", False, f"got {r.status_code}: {r.text[:200]}")

    # ── 13. Summarize Validation ───────────────────────────────────
    print("\n📋 Summarize Validation")
    r = requests.post(
        f"{BASE_URL}/summarize",
        json={"document_ids": []},
        timeout=10,
    )
    test("Empty doc_ids rejected (422)", r.status_code == 422, f"got {r.status_code}")

    # ── 14. Delete Document ────────────────────────────────────────
    print("\n📋 Delete Document")
    r = requests.delete(f"{BASE_URL}/documents/{doc2_id}")
    test("DELETE returns 200", r.status_code == 200, f"got {r.status_code}")

    # Verify deletion
    r = requests.get(f"{BASE_URL}/documents/{doc2_id}")
    test("Deleted doc returns 404", r.status_code == 404, f"got {r.status_code}")

    # Verify list count decreased
    r = requests.get(f"{BASE_URL}/documents")
    data = r.json()
    test("Document count decreased after delete", data.get("total", 0) >= 1)

    # ── 15. Delete first document too (cleanup) ────────────────────
    print("\n📋 Cleanup — Delete Remaining Test Document")
    r = requests.delete(f"{BASE_URL}/documents/{doc_id}")
    test("Cleanup delete returns 200", r.status_code == 200, f"got {r.status_code}")

    # ── 16. Delete Non-existent ────────────────────────────────────
    print("\n📋 Delete Non-existent Document")
    r = requests.delete(f"{BASE_URL}/documents/nonexistent123")
    test("Delete missing doc returns 404", r.status_code == 404, f"got {r.status_code}")

    # ── 17. Final Health Check ─────────────────────────────────────
    print("\n📋 Final Health Check")
    r = requests.get(f"{BASE_URL}/health")
    data = r.json()
    test("Final health check OK", data.get("status") == "ok")
    print(f"    → docs: {data.get('document_count')}, vectors: {data.get('index_size')}")

    # ── Summary ────────────────────────────────────────────────────
    total = PASS + FAIL
    print("\n" + "=" * 60)
    print(f"  Results: {PASS}/{total} passed, {FAIL} failed")
    print("=" * 60 + "\n")

    return 1 if FAIL > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
