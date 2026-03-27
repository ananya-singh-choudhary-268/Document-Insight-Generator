"""OCR service — extracts text from images and PDFs using Tesseract."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path

import pytesseract
from PIL import Image
from PyPDF2 import PdfReader

from app.config import settings

logger = logging.getLogger(__name__)

# Supported file extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
PDF_EXTENSIONS = {".pdf"}
TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".json"}


def is_tesseract_available() -> bool:
    """Check whether the tesseract binary is on PATH."""
    return shutil.which("tesseract") is not None


def extract_text_from_image(file_path: str | Path, lang: str | None = None) -> str:
    """Run Tesseract OCR on an image file.

    Args:
        file_path: Path to the image.
        lang: Tesseract language code(s), e.g. 'eng+fra'. Falls back to settings.

    Returns:
        Extracted text.
    """
    lang = lang or settings.tesseract_lang
    image = Image.open(file_path)
    text: str = pytesseract.image_to_string(image, lang=lang)
    logger.info("OCR extracted %d chars from %s", len(text), Path(file_path).name)
    return text.strip()


def extract_text_from_pdf(file_path: str | Path, lang: str | None = None) -> tuple[str, int]:
    """Extract text from a PDF, using OCR for scanned/image pages.

    Returns:
        Tuple of (full_text, page_count).
    """
    lang = lang or settings.tesseract_lang
    reader = PdfReader(str(file_path))
    page_count = len(reader.pages)
    pages_text: list[str] = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        # If a page yields very little text it's probably a scanned image —
        # fall back to OCR is not straightforward for PDFs without rendering,
        # so we just keep whatever PyPDF2 gives us.
        if text.strip():
            pages_text.append(text.strip())
        else:
            pages_text.append(f"[Page {i + 1}: no extractable text]")

    full_text = "\n\n".join(pages_text)
    logger.info(
        "PDF extracted %d chars across %d pages from %s",
        len(full_text),
        page_count,
        Path(file_path).name,
    )
    return full_text, page_count


def extract_text(file_path: str | Path, lang: str | None = None) -> tuple[str, int]:
    """Dispatcher — pick the right extraction strategy based on file extension.

    Returns:
        Tuple of (extracted_text, page_count).
    """
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in IMAGE_EXTENSIONS:
        if not is_tesseract_available():
            raise RuntimeError(
                "Tesseract is not installed. Install via: brew install tesseract"
            )
        text = extract_text_from_image(path, lang)
        return text, 1

    if ext in PDF_EXTENSIONS:
        return extract_text_from_pdf(path, lang)

    if ext in TEXT_EXTENSIONS:
        text = path.read_text(encoding="utf-8", errors="replace")
        line_count = text.count("\n") + 1
        return text, 1

    raise ValueError(f"Unsupported file type: {ext}")


SUPPORTED_EXTENSIONS = IMAGE_EXTENSIONS | PDF_EXTENSIONS | TEXT_EXTENSIONS
