"""Application configuration loaded from environment variables."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load .env from the backend directory
_backend_dir = Path(__file__).resolve().parent.parent
load_dotenv(_backend_dir / ".env")


class Settings(BaseSettings):
    """Central configuration for the Document Insight Generator."""

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"

    # Directories (relative paths resolved from backend/)
    upload_dir: str = str(_backend_dir / "uploads")
    faiss_index_dir: str = str(_backend_dir / "faiss_index")

    # Text chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200

    # Tesseract OCR
    tesseract_lang: str = "eng"  # e.g. "eng+fra+deu" for multilingual

    # FAISS retrieval
    retrieval_k: int = 4

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

# Ensure required directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.faiss_index_dir, exist_ok=True)
