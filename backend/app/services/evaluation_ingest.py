"""Evaluation ingest — PDF/image → per-page raster images using PyMuPDF."""

from __future__ import annotations

import logging
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError as _e:  # pragma: no cover
    raise ImportError(
        "PyMuPDF is required. Install it with: pip install PyMuPDF"
    ) from _e

try:
    import pytesseract
except ImportError as _e:  # pragma: no cover
    raise ImportError(
        "pytesseract is required. Install it with: pip install pytesseract"
    ) from _e

from PIL import Image

logger = logging.getLogger(__name__)

# DPI for rasterisation — 150 is a good balance of quality vs speed
RENDER_DPI = 150
# PyMuPDF's zoom factor: 150 DPI → zoom = 150/72
_ZOOM = RENDER_DPI / 72.0
_MAT = fitz.Matrix(_ZOOM, _ZOOM)

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}
PDF_EXTENSIONS = {".pdf"}


def _osd_rotate(img: Image.Image) -> tuple[Image.Image, int, bool]:
    """Run Tesseract OSD; return (rotated_image, angle, low_confidence)."""
    try:
        osd = pytesseract.image_to_osd(img, output_type=pytesseract.Output.DICT)
        angle = osd.get("rotate", 0)
        confidence = float(osd.get("orientation_conf", 0))
        low_conf = confidence < 3.0
        if angle and not low_conf:
            img = img.rotate(-angle, expand=True)
        return img, angle, low_conf
    except Exception as exc:
        logger.debug("OSD failed: %s", exc)
        return img, 0, True


def file_to_page_images(file_path: str | Path) -> list[dict]:
    """Render every page of a PDF/image to a PIL Image.

    Returns:
        List of dicts: {page_index, image, low_confidence_orientation}
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    results: list[dict] = []

    if ext in PDF_EXTENSIONS:
        doc = fitz.open(str(path))
        for page_index, page in enumerate(doc):
            pix = page.get_pixmap(matrix=_MAT, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img, angle, low_conf = _osd_rotate(img)
            results.append(
                {
                    "page_index": page_index,
                    "image": img,
                    "low_confidence_orientation": low_conf,
                    "rotation_applied": angle,
                }
            )
        doc.close()

    elif ext in IMAGE_EXTENSIONS:
        img = Image.open(path).convert("RGB")
        img, angle, low_conf = _osd_rotate(img)
        results.append(
            {
                "page_index": 0,
                "image": img,
                "low_confidence_orientation": low_conf,
                "rotation_applied": angle,
            }
        )
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    logger.info("Ingested %d page(s) from %s", len(results), path.name)
    return results
