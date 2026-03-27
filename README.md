# 🔍 Smart Document Insight Generator

A full-stack **GenAI RAG platform** for extracting insights from semi-structured documents using multilingual OCR, vector search, and LLM-powered Q&A/summarization.

## ✨ Features

- **Multilingual OCR** — Extract text from PDFs, images (PNG, JPG, TIFF, BMP), and text files using Tesseract with 12+ language support
- **FAISS Vector Search** — Documents are chunked, embedded, and indexed for fast semantic retrieval
- **Q&A with RAG** — Ask natural language questions and get answers grounded in your documents with source references
- **Document Summarization** — Generate concise AI-powered summaries of one or more documents
- **Modern React UI** — Dark-themed glassmorphic interface with drag-and-drop upload, chat-style Q&A, and responsive design

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React.js, Vite, React Router, Axios |
| Backend | FastAPI, Python, Uvicorn |
| AI/ML | LangChain, OpenAI GPT, FAISS |
| OCR | Tesseract (pytesseract) |
| Data | PyPDF2, Pillow |

## 📦 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point
│   │   ├── config.py               # Environment-based configuration
│   │   ├── models.py               # Pydantic request/response schemas
│   │   ├── routers/                 # API route handlers
│   │   │   ├── documents.py        # Upload, list, delete
│   │   │   ├── query.py            # RAG Q&A
│   │   │   └── summarize.py        # Document summarization
│   │   └── services/               # Business logic
│   │       ├── ocr.py              # Tesseract OCR pipeline
│   │       ├── vectorstore.py      # FAISS index management
│   │       ├── document_processor.py # Ingestion orchestrator
│   │       └── rag.py              # LangChain RAG chains
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── src/
    │   ├── App.jsx
    │   ├── index.css                # Design system
    │   ├── api/client.js            # API wrapper
    │   └── components/
    │       ├── Layout.jsx           # App shell + sidebar
    │       ├── Dashboard.jsx        # Overview + stats
    │       ├── DocumentUpload.jsx   # Drag-and-drop upload
    │       ├── DocumentList.jsx     # Document management
    │       ├── ChatInterface.jsx    # Q&A chat
    │       └── SummaryView.jsx      # Summarization
    └── package.json
```

## 🚀 Getting Started

### Prerequisites

- **Node.js** ≥ 18
- **Python** ≥ 3.10
- **Tesseract OCR**: `brew install tesseract` (macOS) or `apt install tesseract-ocr` (Ubuntu)
- **OpenAI API Key**

### Backend Setup

```bash
cd backend
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
# API docs: http://localhost:8000/docs
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
# App: http://localhost:5173
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload a document for OCR + indexing |
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}` | Get document details |
| DELETE | `/api/documents/{id}` | Delete document + vectors |
| POST | `/api/query` | Ask a question (RAG) |
| POST | `/api/summarize` | Summarize document(s) |
| GET | `/api/health` | System health check |

## 📸 Pages

- **Dashboard** — Stats overview, quick actions, recent documents
- **Upload** — Drag-and-drop with language selection and progress tracking
- **Documents** — Searchable table with status, type, and delete actions
- **Ask Questions** — Chat interface with document filtering and source references
- **Summarize** — Multi-document selector with AI summary generation
