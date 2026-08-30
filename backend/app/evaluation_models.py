"""Evaluation data models (additive — does not touch existing models)."""

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel


# ── Per-page bounding box ───────────────────────────────────────────────────

class BoundingBox(BaseModel):
    left: int = 0
    top: int = 0
    width: int = 0
    height: int = 0


class PageBox(BaseModel):
    page: int = 1
    box: BoundingBox = BoundingBox()


# ── Core domain objects ─────────────────────────────────────────────────────

class Question(BaseModel):
    id: str
    number: str
    sub_part: Optional[str] = None
    text: str
    page: int = 1
    order_index: int = 0
    confidence: str = "high"  # high | low


class AnswerBlock(BaseModel):
    id: str
    label: Optional[str] = None
    text: str = ""
    blocks: list[PageBox] = []
    status: str = "pending_match"  # pending_match | unlabeled_continuation | unmatched_answer


class Mapping(BaseModel):
    question_id: str
    answer_block_id: Optional[str] = None
    match_type: str = "unanswered"  # matched_by_label | matched_by_similarity | unanswered
    confidence: float = 0.0


class GradeResult(BaseModel):
    question_id: str
    marks: float = 0.0
    verdict: str = "incorrect"  # correct | partial | incorrect
    feedback: str = ""


# ── Session ─────────────────────────────────────────────────────────────────

class EvaluationSession(BaseModel):
    id: str
    status: str = "pending"          # pending | processing | done | error
    progress: int = 0                # 0–100
    progress_message: str = ""
    questions: list[Question] = []
    answer_blocks: list[AnswerBlock] = []
    mappings: list[Mapping] = []
    grades: list[GradeResult] = []
    overall_summary: str = ""
    error: Optional[str] = None


# ── API response shapes ─────────────────────────────────────────────────────

class EvaluationUploadResponse(BaseModel):
    session_id: str
    message: str = "Processing started"


class EvaluationStatusResponse(BaseModel):
    session_id: str
    status: str
    progress: int
    progress_message: str
    error: Optional[str] = None


class MappingWithDetails(BaseModel):
    """Mapping enriched with question + answer + grade details for the UI."""
    question: Question
    answer_block: Optional[AnswerBlock] = None
    mapping: Mapping
    grade: Optional[GradeResult] = None


class EvaluationMappingResponse(BaseModel):
    session_id: str
    mappings: list[MappingWithDetails]
    unmatched_answers: list[AnswerBlock]
    overall_summary: str
    total_questions: int
    answered: int
    unanswered: int
    score_percent: float
