# Implementation Plan: Answer Sheet Grading Feature

Base repo: Document-Insight-Generator (FastAPI + React RAG app). Do NOT modify existing OCR/RAG/vectorstore/upload/chat/summarize code. Add new services/routes/components alongside.

## Stack decisions (fixed, do not deviate)
- Handwriting reading: vision LLM (GPT-4o-mini or Gemini Flash), not Tesseract
- Layout/position: Tesseract `image_to_data` (word/line boxes), run in parallel to vision LLM
- PDF→image: PyMuPDF (`fitz`), not pdf2image/poppler
- Backend deploy target: Render/Railway (Tesseract binary needs non-serverless host)
- Storage: in-memory dict keyed by session_id

## Pipeline

### 1. Ingest
- Accept 2 files: question_paper, answer_sheet (PDF or image each)
- Render every page to raster image (PyMuPDF for PDF, passthrough for image)
- Run Tesseract OSD; auto-rotate if confident, else tag page `low_confidence_orientation`
- Emit progress ticks per page (reuse existing upload progress pattern)

### 2. Question extraction (question_paper only)
- Tesseract OCR (printed text) → text + line boxes
- LLM call → strict JSON: `[{number, sub_part, text, page, order_index, confidence}]`
- sub_part is a REQUIRED distinct field — `11(a)` and `11(b)` = 2 entries, never merged
- Regex cross-check on raw OCR (`\d+\s*\([a-z]\)`) vs LLM output; flag mismatches
- Store `number`/`sub_part` verbatim (no renumbering); `order_index` used only for UI sort
- Mark `confidence: low` if underlying OCR word-confidence low for that region

### 3. Answer extraction (answer_sheet only)
- Position pass: Tesseract `image_to_data` per page → line-level boxes (ignore its text accuracy)
- Reading pass: vision LLM transcribes full page, identifies block boundaries via labels (e.g. "Q11", "11(a)", "Ans:") using structural description, not pixel coords
- Alignment: fuzzy-match LLM transcribed lines to Tesseract line boxes → assign real bounding box per answer block
- New block starts only on detected label (regex + LLM agreement); unlabeled text = continuation of previous block, tag `unlabeled_continuation`
- Each answer block: `{label, text, blocks:[{page, box}], status}` — blocks is a list to support multi-page spans
- Blocks with no label match at all → `status: unmatched_answer`, kept, not discarded

### 4. Mapping
- Primary: exact/fuzzy label match (question.number+sub_part vs answer.label)
- Fallback: embedding similarity (reuse existing FAISS/embedding infra) for out-of-order/mislabeled answers
- Every question gets one of: `matched_by_label`, `matched_by_similarity` (flag lower confidence), `unanswered`
- Every leftover answer block with no question match: `unmatched_answer`

### 5. Grading
- Matched Q&A pairs → LLM call → `{marks, verdict: correct|partial|incorrect, feedback}`
- `unanswered` → auto `{marks:0, verdict:incorrect, feedback:"Not answered"}`, no LLM call
- `unmatched_answer` → excluded from score, listed separately for manual review
- One aggregate LLM call → overall summary/feedback across all matched questions

## Data models (new, additive only)
```
Question: {number, sub_part, text, page, order_index, confidence}
AnswerBlock: {label, text, blocks:[{page, box}], status}
Mapping: {question_id, answer_block_id|null, match_type, confidence}
GradeResult: {question_id, marks, verdict, feedback}
EvaluationSession: {id, questions[], answer_blocks[], mappings[], grades[], overall_summary, status}
```

## New API routes (additive)
- `POST /api/evaluation/upload` (2 files) → session_id, starts pipeline
- `GET /api/evaluation/{id}/status` → progress
- `GET /api/evaluation/{id}/questions`
- `GET /api/evaluation/{id}/mapping` (includes grading)

## Frontend (new page, reuse existing design system/components)
- Extend `DocumentUpload.jsx` pattern for 2-file upload w/ progress
- New `EvaluationView.jsx`: left = question list (number, sub_part, status badge: answered/unanswered/low_confidence), right = answer sheet page image + overlay
- Click question → draw overlay box(es) from `mapping.blocks`; if multi-page, show "continues on page N" + let user page through
- Separate section listing `unmatched_answer` blocks
- Grading summary panel (reuse `SummaryView.jsx` layout) — per-question marks + overall summary
- Surface confidence/flags in UI: low_confidence OCR, matched_by_similarity, unlabeled_continuation — do not hide uncertainty

## Explicit edge-case coverage (must all be verifiably handled)
| Requirement | Mechanism |
|---|---|
| Sub-parts as separate entries | Required schema field + regex cross-check |
| Preserve original numbering | Stored verbatim, separate order_index |
| Out-of-order answers | Similarity fallback matching (order-independent) |
| Unanswered questions | Explicit status, auto-zero score |
| Answers matching no question | unmatched_answer, shown not discarded |
| Exact region highlighting | Tesseract boxes + LLM-text alignment |
| Multi-page answers | blocks list per answer, continuation detection |
| Upload progress | Reuse existing progress pattern, new endpoint |

## Known limitations (do not attempt to "fix" beyond this, surface via UI instead)
- OCR/LLM cannot guarantee correct reading of illegible handwriting — mitigate via visible confidence flags, not silent correction
- Unlabeled answers default to "continuation of previous" — surfaced as flagged assumption, not hidden
- Vision LLM free-tier rate limits may throttle on large batch testing
