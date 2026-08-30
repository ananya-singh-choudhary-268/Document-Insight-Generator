"""Mapper — match extracted questions to answer blocks.

Primary strategy: exact / fuzzy label matching.
Fallback: embedding similarity using the existing FAISS/OpenAI embedding infrastructure.
"""

from __future__ import annotations

import logging
from typing import Optional

from rapidfuzz import fuzz, process as fuzz_process
from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


def _question_key(q: dict) -> str:
    """Canonical key for a question: 'number' or 'number_subpart'."""
    num = str(q.get("number", ""))
    sub = (q.get("sub_part") or "").lower()
    return f"{num}_{sub}" if sub else num


def _embedding_similarity(
    client: OpenAI, text_a: str, text_b: str
) -> float:
    """Cosine similarity between two texts using OpenAI embeddings."""
    try:
        resp = client.embeddings.create(
            model="text-embedding-3-small",
            input=[text_a[:2000], text_b[:2000]],
        )
        va = resp.data[0].embedding
        vb = resp.data[1].embedding
        dot = sum(a * b for a, b in zip(va, vb))
        mag_a = sum(a * a for a in va) ** 0.5
        mag_b = sum(b * b for b in vb) ** 0.5
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)
    except Exception as exc:
        logger.warning("Embedding similarity failed: %s", exc)
        return 0.0


def map_questions_to_answers(
    questions: list[dict],
    answer_blocks: list[dict],
) -> list[dict]:
    """Match every question to an answer block.

    Returns a list of Mapping dicts:
        {question_id, answer_block_id|None, match_type, confidence}
    """
    client = OpenAI(api_key=settings.openai_api_key)

    # Index answer blocks by normalised label
    ab_by_label: dict[str, dict] = {}
    for ab in answer_blocks:
        if ab.get("label"):
            ab_by_label[ab["label"]] = ab

    ab_labels = list(ab_by_label.keys())
    mappings: list[dict] = []
    used_ab_ids: set[str] = set()

    for q in questions:
        q_key = _question_key(q)
        q_id = q["id"]

        # ---- 1. Exact match
        if q_key in ab_by_label:
            ab = ab_by_label[q_key]
            mappings.append(
                {
                    "question_id": q_id,
                    "answer_block_id": ab["id"],
                    "match_type": "matched_by_label",
                    "confidence": 1.0,
                }
            )
            used_ab_ids.add(ab["id"])
            continue

        # ---- 2. Fuzzy label match (handles minor formatting differences)
        if ab_labels:
            best_match = fuzz_process.extractOne(
                q_key, ab_labels, scorer=fuzz.ratio
            )
            if best_match and best_match[1] >= 80:
                ab = ab_by_label[best_match[0]]
                mappings.append(
                    {
                        "question_id": q_id,
                        "answer_block_id": ab["id"],
                        "match_type": "matched_by_label",
                        "confidence": best_match[1] / 100.0,
                    }
                )
                used_ab_ids.add(ab["id"])
                continue

        # ---- 3. Embedding similarity fallback (order-independent)
        q_text = q.get("text", "")
        best_ab: Optional[dict] = None
        best_sim: float = 0.0

        for ab in answer_blocks:
            if ab["id"] in used_ab_ids:
                continue
            if ab.get("status") == "unmatched_answer":
                continue
            ab_text = ab.get("text", "")
            if not ab_text.strip():
                continue
            sim = _embedding_similarity(client, q_text, ab_text)
            if sim > best_sim:
                best_sim = sim
                best_ab = ab

        if best_ab and best_sim > 0.6:
            mappings.append(
                {
                    "question_id": q_id,
                    "answer_block_id": best_ab["id"],
                    "match_type": "matched_by_similarity",
                    "confidence": best_sim,
                }
            )
            used_ab_ids.add(best_ab["id"])
        else:
            # Unanswered
            mappings.append(
                {
                    "question_id": q_id,
                    "answer_block_id": None,
                    "match_type": "unanswered",
                    "confidence": 0.0,
                }
            )

    # Tag answer blocks that had no match
    for ab in answer_blocks:
        if ab["id"] not in used_ab_ids:
            ab["status"] = "unmatched_answer"

    logger.info(
        "Mapping complete: %d questions, %d matched, %d unanswered",
        len(questions),
        sum(1 for m in mappings if m["match_type"] != "unanswered"),
        sum(1 for m in mappings if m["match_type"] == "unanswered"),
    )
    return mappings
