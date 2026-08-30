"""Question extractor — Tesseract OCR + LLM structured extraction + regex cross-check."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

import pytesseract
from PIL import Image
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

# Regex: catches "1", "1(a)", "1 (a)", "Q1", "Q1(a)", "11(b)" etc.
_SUBPART_RE = re.compile(
    r"""
    (?:Q|q|Question|QUESTION)?\s*         # optional Q prefix
    (\d+)                                  # main number
    \s*
    (?:
        [\(\[\{]([a-zA-Z]{1,3})[\)\]\}]   # sub-part in brackets: (a), [b], {c}
        |
        \.([ivxIVX]{1,5})                 # roman numeral sub-part: .i  .ii
    )?
    """,
    re.VERBOSE,
)

_LLM_EXTRACTION_SYSTEM = """You are an exam question extractor.
Given OCR text from a question paper, extract ALL questions and sub-questions.
Return ONLY a JSON array — no extra text.

Each element must have exactly these fields:
- number: string, e.g. "1", "11"
- sub_part: string or null, e.g. "a", "b", null
- text: full question text (include options for MCQ)
- page: integer page number (1-indexed)
- order_index: integer, global ordering starting from 1
- confidence: "high" or "low"

Rules:
- Sub-parts like "11(a)" and "11(b)" MUST be separate entries with sub_part = "a" and "b"
- Preserve original numbering exactly — never renumber
- If a question spans multiple lines, concatenate into one text string
- Mark confidence "low" if the OCR text for that question is garbled
"""


def _ocr_page_data(image: Image.Image) -> tuple[str, list[dict]]:
    """Run Tesseract on an image; return (full_text, word_data)."""
    lang = settings.tesseract_lang
    full_text: str = pytesseract.image_to_string(image, lang=lang)
    data = pytesseract.image_to_data(
        image, lang=lang, output_type=pytesseract.Output.DICT
    )
    return full_text, data


def _regex_cross_check(ocr_text: str, llm_questions: list[dict]) -> list[dict]:
    """Detect questions found by regex but missing from LLM output; flag mismatches."""
    regex_found: set[str] = set()
    for m in _SUBPART_RE.finditer(ocr_text):
        num = m.group(1)
        sub = m.group(2) or m.group(3)
        key = f"{num}{'_' + sub.lower() if sub else ''}"
        regex_found.add(key)

    llm_keys: set[str] = set()
    for q in llm_questions:
        sub = (q.get("sub_part") or "").lower() or None
        key = f"{q['number']}{'_' + sub if sub else ''}"
        llm_keys.add(key)

    missing = regex_found - llm_keys
    if missing:
        logger.warning(
            "Regex found question labels not in LLM output: %s", missing
        )
        for q in llm_questions:
            sub = (q.get("sub_part") or "").lower() or None
            key = f"{q['number']}{'_' + sub if sub else ''}"
            if key in missing:
                q["confidence"] = "low"

    return llm_questions


def extract_questions(page_images: list[dict]) -> list[dict]:
    """Extract structured questions from question-paper page images.

    Args:
        page_images: list of dicts from evaluation_ingest.file_to_page_images

    Returns:
        List of Question dicts with keys: id, number, sub_part, text, page,
        order_index, confidence
    """
    client = OpenAI(api_key=settings.openai_api_key)
    all_pages_text: list[str] = []
    all_word_data: list[dict] = []

    # --- Step 1: OCR all pages
    for entry in page_images:
        img = entry["image"]
        page_text, word_data = _ocr_page_data(img)
        all_pages_text.append(page_text)
        all_word_data.append(word_data)
        logger.info("OCR page %d: %d chars", entry["page_index"], len(page_text))

    combined_ocr = "\n\n---PAGE BREAK---\n\n".join(
        f"[Page {i+1}]\n{t}" for i, t in enumerate(all_pages_text)
    )

    # --- Step 2: LLM extraction
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _LLM_EXTRACTION_SYSTEM},
                {
                    "role": "user",
                    "content": f"Extract all questions from this OCR text:\n\n{combined_ocr[:12000]}",
                },
            ],
            temperature=0,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        parsed = json.loads(raw)
        # Handle both array and object wrapping
        if isinstance(parsed, list):
            questions = parsed
        else:
            questions = next(
                (v for v in parsed.values() if isinstance(v, list)), []
            )
    except Exception as exc:
        logger.exception("LLM question extraction failed: %s", exc)
        questions = []

    # --- Step 3: Regex cross-check
    questions = _regex_cross_check(combined_ocr, questions)

    # --- Step 4: Sort & stamp IDs
    questions.sort(key=lambda q: q.get("order_index", 9999))
    result = []
    for i, q in enumerate(questions):
        result.append(
            {
                "id": f"q_{i+1}",
                "number": str(q.get("number", "")),
                "sub_part": q.get("sub_part") or None,
                "text": q.get("text", ""),
                "page": q.get("page", 1),
                "order_index": i + 1,
                "confidence": q.get("confidence", "high"),
            }
        )

    logger.info("Extracted %d questions", len(result))
    return result
