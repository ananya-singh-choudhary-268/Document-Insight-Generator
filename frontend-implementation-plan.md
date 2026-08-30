# Frontend Implementation Plan (from Figma)

Base: existing React/Vite app (Document-Insight-Generator). Reuse existing sidebar/layout (`Layout.jsx`), card styles (`SummaryView.jsx`), upload pattern (`DocumentUpload.jsx`), design system (`index.css`). Do not rewrite framework/routing. Do not migrate to Next.js.

## Screen 1: Upload
- Icon sidebar (logo + nav icons) unchanged from existing layout
- Centered card: "Upload Question Paper & Answer Sheets"
- TWO separate drop zones (not one combined uploader): "Upload Question Paper" and "Upload Answer Sheets"
- On file select: show file chip (icon + filename + size + remove button) per slot
- Continue/"Get Started" button disabled until both files present

## Screen 2: Processing
- Full-screen centered state: sparkle/AI icon + "Extracting..." + subtext (e.g. "this may take a while")
- No percentage progress bar — simple loading state only

## Screen 3: Question–Answer Mapping (main workspace)
Layout: left icon rail | left panel (questions) | right panel (answer sheet)

**Top bar:** back arrow, breadcrumb ("Exams"), right-aligned help/notification/AI/user-avatar icons

**Left icon rail:** logo, AI/sparkle icon (active/highlighted state), grid, cursor, doc, clipboard, history icons

**Left panel — "Extracted Questions (from question paper)" + "Expand All" button**
- Each row: numbered circle badge, question text, score badge as fraction "x/y", chevron to expand
- Score badge color: green = full marks, orange = partial, red = zero/incorrect
- Sub-parts (e.g. 11a/11b): separate rows, same number badge ("11") + letter label ("a.", "b.") — never merged into one row
- Expanded/selected row: orange left border/highlight, shows "AI Feedback" section with feedback text below
- Unanswered question: red "0/max" badge, row clearly marked "not answered", no box drawn on right panel when selected
- Unmatched answer blocks: separate section/list below the question list (not shown as a numbered question)
- Confidence flags (low_confidence OCR, matched_by_similarity, unlabeled_continuation): small icon/tag on the row — do not hide uncertainty

**Right panel — "Answer Sheet"**
- Header: zoom controls (– 100% +), page nav ("Page 1 of 4", prev/next arrows)
- Scanned answer image, continuously scrollable across pages
- Selected question → colored bounding box drawn on its answer region + small tag label above box (e.g. green "Q2" tag); box color matches that question's score badge color
- Multi-page answers: box renders on each relevant page; page nav lets teacher move through

## Components to build/extend
- Extend `DocumentUpload.jsx` → 2-slot upload variant
- New `EvaluationView.jsx` → Screen 3 (question list + answer sheet panel + overlay boxes)
- New `AnswerSheetViewer.jsx` → image render + zoom/page controls + overlay box rendering (given box coords + color from API)
- New `QuestionListItem.jsx` → row w/ badge, score, expand, AI feedback panel
- Reuse `SummaryView.jsx` card styling for AI Feedback block

## API contract expected by frontend (backend-owned, not built here)
- `POST /api/evaluation/upload` (2 files) → `session_id`
- `GET /api/evaluation/{id}/status` → processing state
- `GET /api/evaluation/{id}/questions` → question list w/ scores
- `GET /api/evaluation/{id}/mapping` → per-question: answer text, box coords (per page), box_color, status, feedback

## Deployment (frontend)
- `npm run build` → deploy `dist/` to Vercel or Netlify (Vite auto-detected)
- Set backend base URL via env var (`VITE_API_URL` or existing `api/client.js` config) at build time
- No frontend framework change needed for deployment simplicity — backend requires Python regardless
