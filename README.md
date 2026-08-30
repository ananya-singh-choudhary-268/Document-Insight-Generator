# 🔍 Smart Document Insight Generator

**Live Deployment:** [https://document-insight-generator-lake.vercel.app/](https://document-insight-generator-lake.vercel.app/)

A full-stack **GenAI platform** for extracting insights from semi-structured documents. It features multilingual OCR, FAISS vector search, LLM-powered Q&A/summarization, and an **Automated Answer Sheet Grading** pipeline.

## ✨ Features

- **Automated Answer Sheet Grading (New)** — Upload a question paper and a student's answer sheet. The system extracts questions, identifies handwritten answer regions, maps them together using AI/fuzzy matching, and grades the answers using an LLM. Includes a visual viewer with color-coded bounding boxes.
- **Multilingual OCR** — Extract text from PDFs, images (PNG, JPG, TIFF, BMP), and text files using Tesseract with 12+ language support and PyMuPDF.
- **FAISS Vector Search** — Documents are chunked, embedded, and indexed for fast semantic retrieval.
- **Q&A with RAG** — Ask natural language questions and get answers grounded in your documents with source references.
- **Document Summarization** — Generate concise AI-powered summaries of one or more documents.
- **Modern React UI** — Dark-themed glassmorphic interface with drag-and-drop upload, chat-style Q&A, answer sheet workspace, and responsive design.

## 🏗️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React.js, Vite, React Router, Axios, CSS Modules |
| Backend | FastAPI, Python, Uvicorn |
| AI/ML | LangChain, OpenAI (GPT-4o-mini), FAISS |
| OCR / Vision | Tesseract (pytesseract), PyMuPDF (fitz), Pillow, GPT-4o-mini (Vision) |
| Matching | RapidFuzz, OpenAI Embeddings |
| Deployment | Vercel (Frontend), Render/Railway (Backend Docker) |

## 📦 Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app entry point (CORS + routing)
│   │   ├── config.py               # Environment configuration
│   │   ├── models.py               # Pydantic schemas (base)
│   │   ├── evaluation_models.py    # Pydantic schemas for grading pipeline
│   │   ├── routers/                # API route handlers
│   │   │   ├── documents.py        # Upload, list, delete
│   │   │   ├── query.py            # RAG Q&A
│   │   │   ├── summarize.py        # Document summarization
│   │   │   └── evaluation.py       # Answer sheet grading pipeline
│   │   └── services/               # Core business logic
│   │       ├── ocr.py              # Base Tesseract OCR
│   │       ├── vectorstore.py      # FAISS index management
│   │       ├── document_processor.py
│   │       ├── rag.py              # LangChain Q&A
│   │       ├── evaluation_ingest.py # PDF/Image to Raster (PyMuPDF)
│   │       ├── question_extractor.py # OCR + LLM Question parsing
│   │       ├── answer_extractor.py # Vision LLM + Layout box parsing
│   │       ├── mapper.py           # Fuzzy/Embedding Question→Answer mapping
│   │       └── grader.py           # LLM answer evaluation
│   ├── Dockerfile                  # Production Docker configuration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── index.css               # Design system & tokens
│   │   ├── api/
│   │   │   ├── client.js           # Base Axios client
│   │   │   └── evaluationClient.js # Endpoints for grading
│   │   └── components/
│   │       ├── Layout.jsx          # App shell + sidebar
│   │       ├── DocumentUpload.jsx  # Base document ingestion
│   │       ├── ChatInterface.jsx   # RAG Q&A chat
│   │       ├── EvaluationUpload.jsx# 2-slot drag & drop upload
│   │       ├── EvaluationView.jsx  # Grading results workspace
│   │       ├── QuestionListItem.jsx# Score badge & AI feedback row
│   │       └── AnswerSheetViewer.jsx # Zoomable canvas with box overlay
│   └── package.json
├── render.yaml                     # IaC for Render deployment
├── railway.json                    # IaC for Railway deployment
├── vercel.json                     # IaC for Vercel deployment
└── netlify.toml                    # IaC for Netlify deployment
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

### Documents & RAG
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/documents/upload` | Upload a document for OCR + indexing |
| GET | `/api/documents` | List all documents |
| GET | `/api/documents/{id}` | Get document details |
| DELETE | `/api/documents/{id}` | Delete document + vectors |
| POST | `/api/query` | Ask a question (RAG) |
| POST | `/api/summarize` | Summarize document(s) |

### Automated Evaluation (Grading)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/evaluation/upload` | Upload question paper + answer sheet |
| GET | `/api/evaluation/{session_id}/status` | Check pipeline processing status |
| GET | `/api/evaluation/{session_id}/questions`| Get extracted questions |
| GET | `/api/evaluation/{session_id}/mapping`  | Get full grading results & mapping |
| GET | `/api/evaluation/{session_id}/pages`    | Get answer sheet images |

## 📸 Modules

- **Dashboard** — Stats overview, quick actions, recent documents.
- **Documents & Q&A** — Upload documents, manage your library, and chat with them using semantic RAG.
- **Answer Sheet Evaluation (New)** — Upload a blank exam paper alongside a handwritten answer sheet. The system extracts questions, locates answers, maps them together, grades them using LLMs, and presents a visual workspace with score badges, AI feedback, and a zoomable bounding-box viewer.
