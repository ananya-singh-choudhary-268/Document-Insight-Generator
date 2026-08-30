import { useState } from 'react';
import {
  HiOutlineChevronDown,
  HiOutlineChevronUp,
  HiOutlineExclamationCircle,
  HiOutlineLightBulb,
  HiOutlineMinusCircle,
} from 'react-icons/hi';

/* Score badge as fraction x/y — color by verdict */
function ScoreBadge({ marks, verdict, unanswered }) {
  const pct = Math.round((marks ?? 0) * 100);
  const cls =
    unanswered || verdict === 'incorrect'
      ? 'qli-badge--red'
      : verdict === 'partial'
      ? 'qli-badge--orange'
      : 'qli-badge--green';

  // Show as "x/10" — we don't have per-question max, so show pct/100 style
  return (
    <span className={`qli-badge ${cls}`}>
      {pct}<span className="qli-badge-denom">/100</span>
    </span>
  );
}

/* Confidence flag icons */
function ConfidenceFlags({ question, mapping }) {
  const flags = [];
  if (question.confidence === 'low') flags.push('Low OCR confidence');
  if (mapping.match_type === 'matched_by_similarity') flags.push('AI-matched (not exact label)');
  if (!flags.length) return null;
  return (
    <div className="qli-flags">
      {flags.map((f) => (
        <span key={f} className="qli-flag" title={f}>
          <HiOutlineExclamationCircle />
          <span>{f}</span>
        </span>
      ))}
    </div>
  );
}

export default function QuestionListItem({ mapping, selected, onSelect }) {
  const [expanded, setExpanded] = useState(false);
  const { question: q, grade, answer_block: ab, mapping: m } = mapping;
  const isUnanswered = m.match_type === 'unanswered';
  const isContinuation = ab?.status === 'unlabeled_continuation';

  const toggle = (e) => {
    e.stopPropagation();
    setExpanded((v) => !v);
    onSelect(); // selecting also expands detail on right
  };

  return (
    <div
      className={`qli ${selected ? 'qli--selected' : ''} ${isUnanswered ? 'qli--unanswered' : ''}`}
      onClick={onSelect}
      id={`q-item-${q.id}`}
    >
      {/* Left accent bar (shows on selected) */}
      <div className="qli-accent" />

      {/* Number badge */}
      <div className="qli-num">
        <span className="qli-num-main">{q.number}</span>
        {q.sub_part && <span className="qli-num-sub">{q.sub_part}.</span>}
      </div>

      {/* Main content */}
      <div className="qli-body">
        <div className="qli-row1">
          <span className="qli-qtext">{q.text || <em>No text extracted</em>}</span>
          {grade && (
            <ScoreBadge marks={grade.marks} verdict={grade.verdict} unanswered={isUnanswered} />
          )}
          {isUnanswered && !grade && (
            <span className="qli-badge qli-badge--red">Not answered</span>
          )}
          <button
            className="qli-chevron"
            onClick={toggle}
            title={expanded ? 'Collapse' : 'Expand'}
          >
            {expanded ? <HiOutlineChevronUp /> : <HiOutlineChevronDown />}
          </button>
        </div>

        {/* Confidence flags */}
        <ConfidenceFlags question={q} mapping={m} />

        {/* Unanswered notice */}
        {isUnanswered && (
          <div className="qli-unanswered-note">
            <HiOutlineMinusCircle />
            Not answered
          </div>
        )}

        {/* Expanded: AI feedback */}
        {expanded && grade && !isUnanswered && (
          <div className="qli-feedback">
            <div className="qli-feedback-label">
              <HiOutlineLightBulb />
              AI Feedback
            </div>
            <div className="qli-feedback-text">{grade.feedback}</div>
            {isContinuation && (
              <div className="qli-flag" style={{ marginTop: 4 }}>
                <HiOutlineExclamationCircle />
                <span>Unlabeled continuation — check region carefully</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
