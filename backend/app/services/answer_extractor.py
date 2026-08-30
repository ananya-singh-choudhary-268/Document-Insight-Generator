"""Answer extractor — Tesseract layout (bounding boxes) + Vision LLM reading + alignment."""

from __future__ import annotations

import base64
import io
import json
import logging
import re
from typing import Any

import pytesseract
from PIL import Image
from openai import OpenAI
from rapidfuzz import fuzz

from app.config import settings

logger = logging.getLogger(__name__)

# Regex to detect answer block labels written by students
# Matches: Q1, 1, 1(a), 1a, Ans 1, Answer 1, Q.1(a) etc.
_LABEL_RE = re.compile(
    r"""
    ^\s*                                    # start of (stripped) line
    (?:Q(?:uestion)?\.?\s*|Ans(?:wer)?\.?\s*)?   # optional prefix
    (\d+)                                   # main number
    \s*
    (?:
        [\(\[\.]([a-zA-Z]{1,3})[\)\]]?      # sub-part
    )?
    \s*[:\-\.\)]?\s*$                       # optional trailing separator
    """,
    re.VERBOSE | re.IGNORECASE,
)

_VISION_SYSTEM = """You are an expert at reading handwritten exam answer sheets.
Given an image of one page of an answer sheet, extract ALL written content.

Return ONLY a JSON object with this structure:
{
  "blocks": [
    {
      "label": "1(a)",         // The question label the student wrote (e.g. "1", "2(b)", "Q3"). null if unlabeled continuation.
      "text": "Full transcribed text of this answer block",
      "is_unlabeled_continuation": false  // true if no clear label — treat as continuation of previous block
    }
  ]
}

Rules:
- Each new answer block starts when the student writes a new question label
- If text has no label and follows a labeled block, set is_unlabeled_continuation=true
- Transcribe handwriting as accurately as possible
- Keep original structure; do not merge separate answer blocks
"""


def _image_to_base64(img: Image.Image) -> str:
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def _get_line_boxes(image: Image.Image) -> list[dict]:
    """Run Tesseract image_to_data; return line-level bounding boxes."""
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        lang=settings.tesseract_lang,
    )
    lines: list[dict] = []
    n = len(data["level"])
    for i in range(n):
        if data["level"][i] == 4:  # line level
            lines.append(
                {
                    "left": data["left"][i],
                    "top": data["top"][i],
                    "width": data["width"][i],
                    "height": data["height"][i],
                    "text": data["text"][i],
                }
            )
    return lines


def _align_blocks_to_boxes(
    blocks: list[dict], line_boxes: list[dict], page_index: int, img_size: tuple[int, int]
) -> list[dict]:
    """
    For each block returned by the LLM, find the best-matching Tesseract line box
    to get a real bounding box. Falls back to full-page box if nothing aligns.
    """
    img_w, img_h = img_size
    full_page_box = {"left": 0, "top": 0, "width": img_w, "height": img_h}

    for block in blocks:
        block_text = (block.get("text") or "").strip()
        label = (block.get("label") or "").strip()
        search_token = label or block_text[:40]

        best_score = 0
        best_box = None
        for lb in line_boxes:
            lb_text = (lb.get("text") or "").strip()
            if not lb_text:
                continue
            score = fuzz.partial_ratio(search_token.lower(), lb_text.lower())
            if score > best_score:
                best_score = score
                best_box = lb

        if best_box and best_score > 40:
            bx = {
                "left": best_box["left"],
                "top": best_box["top"],
                "width": best_box["width"],
                "height": best_box["height"],
            }
        else:
            bx = full_page_box

        block["page_box"] = {"page": page_index + 1, "box": bx}

    return blocks


def extract_answers(page_images: list[dict]) -> list[dict]:
    """Extract answer blocks from answer-sheet page images.

    Returns a list of AnswerBlock dicts:
        {id, label, text, blocks:[{page, box}], status}
    """
    client = OpenAI(api_key=settings.openai_api_key)
    all_page_blocks: list[list[dict]] = []

    for entry in page_images:
        img: Image.Image = entry["image"]
        page_index: int = entry["page_index"]

        # --- Layout pass (Tesseract)
        line_boxes = _get_line_boxes(img)
        logger.info("Page %d: got %d Tesseract line boxes", page_index, len(line_boxes))

        # --- Reading pass (vision LLM)
        b64 = _image_to_base64(img)
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _VISION_SYSTEM},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{b64}",
                                    "detail": "high",
                                },
                            },
                            {
                                "type": "text",
                                "text": "Extract all answer blocks from this exam answer sheet page.",
                            },
                        ],
                    },
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            raw = response.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            page_blocks: list[dict] = parsed.get("blocks", [])
        except Exception as exc:
            logger.exception("Vision LLM failed on page %d: %s", page_index, exc)
            page_blocks = []

        # --- Alignment
        page_blocks = _align_blocks_to_boxes(
            page_blocks, line_boxes, page_index, img.size
        )
        all_page_blocks.append(page_blocks)

    # --- Merge blocks across pages into AnswerBlock objects
    # Blocks with same label on different pages are merged (multi-page answer)
    answer_blocks: dict[str, dict] = {}  # label → AnswerBlock
    unmatched: list[dict] = []
    ab_id_counter = 1

    for page_index, page_blocks in enumerate(all_page_blocks):
        prev_label: str | None = None

        for block in page_blocks:
            label = (block.get("label") or "").strip() or None
            text = (block.get("text") or "").strip()
            is_continuation = block.get("is_unlabeled_continuation", False)
            page_box = block.get("page_box", {})

            if is_continuation or label is None:
                # Continuation — attach to previous block
                if prev_label and prev_label in answer_blocks:
                    answer_blocks[prev_label]["text"] += "\n" + text
                    answer_blocks[prev_label]["blocks"].append(page_box)
                    answer_blocks[prev_label]["status"] = "unlabeled_continuation"
                else:
                    unmatched.append(
                        {
                            "id": f"ab_{ab_id_counter}",
                            "label": None,
                            "text": text,
                            "blocks": [page_box],
                            "status": "unmatched_answer",
                        }
                    )
                    ab_id_counter += 1
                continue

            # Normalise label
            norm_label = _normalise_label(label)
            if norm_label in answer_blocks:
                # Continuation of the same question on a new page
                answer_blocks[norm_label]["text"] += "\n" + text
                answer_blocks[norm_label]["blocks"].append(page_box)
            else:
                answer_blocks[norm_label] = {
                    "id": f"ab_{ab_id_counter}",
                    "label": norm_label,
                    "text": text,
                    "blocks": [page_box],
                    "status": "pending_match",
                }
                ab_id_counter += 1

            prev_label = norm_label

    result = list(answer_blocks.values()) + unmatched
    logger.info(
        "Extracted %d answer blocks (%d unmatched)", len(answer_blocks), len(unmatched)
    )
    return result


def _normalise_label(label: str) -> str:
    """Normalise a student-written label for matching: '1(a)' → '1_a', 'Q2' → '2'."""
    label = label.strip().upper()
    # Remove Q prefix
    label = re.sub(r"^Q\.?\s*", "", label)
    # Normalise sub-part
    m = re.match(r"(\d+)\s*[\(\[\.]?\s*([A-Z]{1,3})[\)\]]?", label)
    if m:
        return f"{m.group(1)}_{m.group(2).lower()}"
    # Just number
    m2 = re.match(r"(\d+)", label)
    if m2:
        return m2.group(1)
    return label.lower()
