"""Grader — per-question LLM grading + overall session summary."""

from __future__ import annotations

import json
import logging

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)

_GRADE_SYSTEM = """You are an expert exam grader.
Given a question and a student's handwritten answer (transcribed), evaluate the answer.

Return ONLY a JSON object with:
{
  "marks": <float, 0.0–1.0 where 1.0 = full marks>,
  "verdict": "<correct|partial|incorrect>",
  "feedback": "<concise 1-3 sentence feedback>"
}

Be strict but fair. Partial credit for partially correct answers.
"""

_SUMMARY_SYSTEM = """You are an academic evaluator.
Given a list of question–answer grading results, write an overall evaluation summary.

Return plain text (3-5 sentences) covering:
- Overall performance
- Strongest areas
- Areas needing improvement
- Suggestions for the student
"""


def grade_session(
    questions: list[dict],
    answer_blocks: list[dict],
    mappings: list[dict],
) -> tuple[list[dict], str]:
    """Grade all matched Q&A pairs and produce an overall summary.

    Returns:
        (grade_results, overall_summary)
        grade_results: list of GradeResult dicts
    """
    client = OpenAI(api_key=settings.openai_api_key)

    # Build look-up tables
    q_by_id = {q["id"]: q for q in questions}
    ab_by_id = {ab["id"]: ab for ab in answer_blocks}

    grade_results: list[dict] = []
    grading_context_parts: list[str] = []

    for mapping in mappings:
        q_id = mapping["question_id"]
        ab_id = mapping.get("answer_block_id")
        match_type = mapping["match_type"]
        q = q_by_id.get(q_id, {})
        q_text = q.get("text", "")
        q_label = f"Q{q.get('number','')}" + (
            f"({q.get('sub_part')})" if q.get("sub_part") else ""
        )

        if match_type == "unanswered" or ab_id is None:
            grade_results.append(
                {
                    "question_id": q_id,
                    "marks": 0.0,
                    "verdict": "incorrect",
                    "feedback": "Not answered.",
                }
            )
            grading_context_parts.append(
                f"{q_label}: [NOT ANSWERED]"
            )
            continue

        ab = ab_by_id.get(ab_id, {})
        ab_text = ab.get("text", "").strip()

        try:
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": _GRADE_SYSTEM},
                    {
                        "role": "user",
                        "content": (
                            f"Question: {q_text}\n\n"
                            f"Student's answer: {ab_text[:3000]}"
                        ),
                    },
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content or "{}"
            result = json.loads(raw)
            marks = float(result.get("marks", 0.0))
            verdict = result.get("verdict", "incorrect")
            feedback = result.get("feedback", "")
        except Exception as exc:
            logger.exception("Grading failed for %s: %s", q_id, exc)
            marks, verdict, feedback = 0.0, "incorrect", "Grading error."

        grade_results.append(
            {
                "question_id": q_id,
                "marks": marks,
                "verdict": verdict,
                "feedback": feedback,
            }
        )
        grading_context_parts.append(
            f"{q_label} [{verdict}, marks={marks:.1f}]: Q: {q_text[:200]} | A: {ab_text[:200]}"
        )

    # --- Overall summary
    context = "\n\n".join(grading_context_parts[:30])  # cap token usage
    try:
        summary_resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SUMMARY_SYSTEM},
                {"role": "user", "content": f"Grading results:\n{context}"},
            ],
            temperature=0.3,
        )
        overall_summary = summary_resp.choices[0].message.content or ""
    except Exception as exc:
        logger.exception("Overall summary failed: %s", exc)
        overall_summary = "Unable to generate summary."

    logger.info(
        "Grading done: %d results, avg marks=%.2f",
        len(grade_results),
        sum(g["marks"] for g in grade_results) / max(len(grade_results), 1),
    )
    return grade_results, overall_summary
