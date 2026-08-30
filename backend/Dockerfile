# ────────────────────────────────────────────────────────────────────────────
# Document Insight Generator — Backend  (Python 3.12 · FastAPI · Tesseract)
# ────────────────────────────────────────────────────────────────────────────
# Build:  docker build -t dig-backend .
# Run:    docker run -p 8000:8000 --env-file .env dig-backend
# ────────────────────────────────────────────────────────────────────────────

FROM python:3.12-slim

# System deps: Tesseract + its English data + PDF libs used by PyMuPDF
RUN apt-get update && apt-get install -y --no-install-recommends \
        tesseract-ocr \
        tesseract-ocr-eng \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (cached layer unless requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/

# Runtime directories (Render/Railway mount ephemeral storage here)
RUN mkdir -p uploads faiss_index

# Expose port (Render auto-injects $PORT; we default to 8000)
EXPOSE 8000

# Start — use $PORT if set (Render), else 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
