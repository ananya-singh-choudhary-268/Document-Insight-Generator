"""Evaluation router — additive endpoints for the answer-sheet grading pipeline."""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from PIL import Image

from app.config import settings
from app.evaluation_models import (
    AnswerBlock,
    EvaluationMappingResponse,
    EvaluationSession,
    EvaluationStatusResponse,
    EvaluationUploadResponse,
    GradeResult,
    Mapping,
    MappingWithDetails,
    PageBox,
    BoundingBox,
    Question,
)
from app.services import evaluation_ingest, question_extractor, answer_extractor, mapper, grader

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])

# ── In-memory session store ────────────────────────────────────────────────
_sessions: dict[str, EvaluationSession] = {}

# ── Image cache for the UI (base64 page images) ───────────────────────────
_page_images_cache: dict[str, list[dict]] = {}  # session_id → [{page, b64}]

SUPPORTED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif", ".bmp", ".webp"}


def _validate_ext(filename: str) -> str:
    ext = Path(filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: {', '.join(sorted(SUPPORTED_EXTENSIONS))}",
        )
    return ext


def _img_to_b64(img: Image.Image) -> str:
    buf = io.BytesIO()
    # Resize for transfer efficiency (max 1600px wide)
    w, h = img.size
    if w > 1600:
        img = img.resize((1600, int(h * 1600 / w)), Image.LANCZOS)
    img.save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


async def _run_pipeline(
    session_id: str,
    qp_bytes: bytes,
    qp_ext: str,
    as_bytes: bytes,
    as_ext: str,
) -> None:
    """Background task: run the full evaluation pipeline and update session."""
    session = _sessions[session_id]

    def _tick(pct: int, msg: str) -> None:
        session.progress = pct
        session.progress_message = msg
        logger.info("[%s] %d%% — %s", session_id, pct, msg)

    try:
        session.status = "processing"

        # ── 1. Ingest question paper
        _tick(5, "Rendering question paper pages…")
        upload_dir = Path(settings.upload_dir) / "evaluation" / session_id
        upload_dir.mkdir(parents=True, exist_ok=True)

        qp_path = upload_dir / f"question_paper{qp_ext}"
        qp_path.write_bytes(qp_bytes)
        as_path = upload_dir / f"answer_sheet{as_ext}"
        as_path.write_bytes(as_bytes)

        qp_pages = evaluation_ingest.file_to_page_images(qp_path)
        _tick(15, f"Rendered {len(qp_pages)} question-paper page(s).")

        # ── 2. Extract questions
        _tick(20, "Extracting questions with OCR + AI…")
        raw_questions = question_extractor.extract_questions(qp_pages)
        questions = [Question(**q) for q in raw_questions]
        session.questions = questions
        _tick(40, f"Extracted {len(questions)} question(s).")

        # ── 3. Ingest answer sheet
        _tick(45, "Rendering answer sheet pages…")
        as_pages = evaluation_ingest.file_to_page_images(as_path)

        # Cache answer-sheet page images for the UI overlay
        _page_images_cache[session_id] = [
            {"page": e["page_index"] + 1, "b64": _img_to_b64(e["image"])}
            for e in as_pages
        ]
        _tick(55, f"Rendered {len(as_pages)} answer-sheet page(s).")

        # ── 4. Extract answers
        _tick(60, "Reading handwritten answers with vision AI…")
        raw_abs = answer_extractor.extract_answers(as_pages)
        abs_list = []
        for ab in raw_abs:
            page_boxes = []
            for pb in ab.get("blocks", []):
                box = pb.get("box", {})
                page_boxes.append(
                    PageBox(
                        page=pb.get("page", 1),
                        box=BoundingBox(
                            left=box.get("left", 0),
                            top=box.get("top", 0),
                            width=box.get("width", 0),
                            height=box.get("height", 0),
                        ),
                    )
                )
            abs_list.append(
                AnswerBlock(
                    id=ab["id"],
                    label=ab.get("label"),
                    text=ab.get("text", ""),
                    blocks=page_boxes,
                    status=ab.get("status", "pending_match"),
                )
            )
        session.answer_blocks = abs_list
        _tick(70, f"Extracted {len(abs_list)} answer block(s).")

        # ── 5. Mapping
        _tick(75, "Mapping questions to answers…")
        raw_mappings = mapper.map_questions_to_answers(
            [q.model_dump() for q in questions],
            [ab.model_dump() for ab in abs_list],
        )
        mappings = [Mapping(**m) for m in raw_mappings]
        session.mappings = mappings

        # Update answer block statuses from mapper
        ab_by_id = {ab.id: ab for ab in abs_list}
        for ab_raw in raw_abs:
            ab_id = ab_raw["id"]
            if ab_id in ab_by_id:
                ab_by_id[ab_id].status = ab_raw.get("status", ab_by_id[ab_id].status)

        _tick(80, "Mapping complete.")

        # ── 6. Grading
        _tick(85, "Grading answers with AI…")
        raw_grades, overall_summary = grader.grade_session(
            [q.model_dump() for q in questions],
            [ab.model_dump() for ab in abs_list],
            [m.model_dump() for m in mappings],
        )
        session.grades = [GradeResult(**g) for g in raw_grades]
        session.overall_summary = overall_summary
        _tick(100, "Grading complete.")

        session.status = "done"

    except Exception as exc:
        logger.exception("Pipeline failed for session %s", session_id)
        session.status = "error"
        session.error = str(exc)
        session.progress_message = f"Error: {exc}"


# ── API Routes ─────────────────────────────────────────────────────────────


@router.post("/upload", response_model=EvaluationUploadResponse)
async def upload_evaluation(
    background_tasks: BackgroundTasks,
    question_paper: UploadFile = File(...),
    answer_sheet: UploadFile = File(...),
):
    """Upload question paper + answer sheet; start the evaluation pipeline."""
    qp_ext = _validate_ext(question_paper.filename or "")
    as_ext = _validate_ext(answer_sheet.filename or "")

    qp_bytes = await question_paper.read()
    as_bytes = await answer_sheet.read()

    session_id = uuid.uuid4().hex[:12]
    _sessions[session_id] = EvaluationSession(
        id=session_id,
        status="pending",
        progress=0,
        progress_message="Queued…",
    )

    background_tasks.add_task(
        _run_pipeline, session_id, qp_bytes, qp_ext, as_bytes, as_ext
    )

    return EvaluationUploadResponse(
        session_id=session_id, message="Processing started"
    )


@router.get("/{session_id}/status", response_model=EvaluationStatusResponse)
async def get_status(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return EvaluationStatusResponse(
        session_id=session_id,
        status=session.status,
        progress=session.progress,
        progress_message=session.progress_message,
        error=session.error,
    )


@router.get("/{session_id}/questions")
async def get_questions(session_id: str):
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session_id": session_id, "questions": [q.model_dump() for q in session.questions]}


@router.get("/{session_id}/pages")
async def get_answer_sheet_pages(session_id: str):
    """Return base64-encoded JPEG images of the answer sheet pages for the UI overlay."""
    if session_id not in _page_images_cache:
        raise HTTPException(status_code=404, detail="Page images not ready yet")
    return {"session_id": session_id, "pages": _page_images_cache[session_id]}


@router.get("/{session_id}/mapping", response_model=EvaluationMappingResponse)
async def get_mapping(session_id: str):
    """Full evaluation result — mappings, grades, unmatched answers, summary."""
    session = _sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session.status not in ("done", "error"):
        raise HTTPException(status_code=202, detail="Processing not complete yet")

    q_by_id = {q.id: q for q in session.questions}
    ab_by_id = {ab.id: ab for ab in session.answer_blocks}
    grade_by_qid = {g.question_id: g for g in session.grades}

    enriched: list[MappingWithDetails] = []
    for m in session.mappings:
        q = q_by_id.get(m.question_id)
        if not q:
            continue
        ab = ab_by_id.get(m.answer_block_id) if m.answer_block_id else None
        grade = grade_by_qid.get(m.question_id)
        enriched.append(
            MappingWithDetails(question=q, answer_block=ab, mapping=m, grade=grade)
        )

    unmatched = [ab for ab in session.answer_blocks if ab.status == "unmatched_answer"]

    total = len(session.questions)
    answered = sum(1 for m in session.mappings if m.match_type != "unanswered")
    unanswered = total - answered
    total_marks = sum(g.marks for g in session.grades)
    score_pct = (total_marks / max(total, 1)) * 100

    return EvaluationMappingResponse(
        session_id=session_id,
        mappings=enriched,
        unmatched_answers=unmatched,
        overall_summary=session.overall_summary,
        total_questions=total,
        answered=answered,
        unanswered=unanswered,
        score_percent=round(score_pct, 1),
    )
