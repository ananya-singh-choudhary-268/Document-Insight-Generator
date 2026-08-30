import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  getEvaluationStatus,
  getEvaluationMapping,
  getEvaluationPages,
} from '../api/evaluationClient';
import QuestionListItem from './QuestionListItem';
import AnswerSheetViewer from './AnswerSheetViewer';
import {
  HiOutlineSparkles,
  HiOutlineArrowLeft,
  HiOutlineExclamationCircle,
  HiOutlineCheckCircle,
  HiOutlineChevronDown,
} from 'react-icons/hi';

/* ─── Screen 2: Processing ──────────────────────────────────────────────── */
function ProcessingScreen({ message }) {
  return (
    <div className="ev-processing">
      <div className="ev-processing-inner">
        <div className="ev-processing-icon">
          <HiOutlineSparkles />
          <span className="ev-processing-ring" />
        </div>
        <h2 className="ev-processing-title">Extracting…</h2>
        <p className="ev-processing-sub">
          {message || 'AI is reading the question paper and answer sheet — this may take a while'}
        </p>
      </div>
    </div>
  );
}

/* ─── Error screen ──────────────────────────────────────────────────────── */
function ErrorScreen({ error, onBack }) {
  return (
    <div className="ev-processing">
      <div className="ev-processing-inner">
        <div className="ev-processing-icon ev-processing-icon--error">
          <HiOutlineExclamationCircle />
        </div>
        <h2 className="ev-processing-title">Processing Failed</h2>
        <p className="ev-processing-sub">{error}</p>
        <button className="btn btn-secondary" style={{ marginTop: 'var(--space-6)' }} onClick={onBack}>
          <HiOutlineArrowLeft /> Try Again
        </button>
      </div>
    </div>
  );
}

/* ─── Top bar ────────────────────────────────────────────────────────────── */
function TopBar({ onBack, answered, unanswered, total, score }) {
  return (
    <div className="ev-topbar">
      <div className="ev-topbar-left">
        <button className="ev-back-btn" onClick={onBack} title="Back to upload">
          <HiOutlineArrowLeft />
        </button>
        <div className="ev-breadcrumb">
          <span className="ev-breadcrumb-parent">Exams</span>
          <span className="ev-breadcrumb-sep">/</span>
          <span className="ev-breadcrumb-current">Evaluation Results</span>
        </div>
      </div>
      <div className="ev-topbar-stats">
        <div className="ev-stat">
          <span className="ev-stat-val">{total}</span>
          <span className="ev-stat-lbl">Total</span>
        </div>
        <div className="ev-stat">
          <span className="ev-stat-val ev-stat-val--green">{answered}</span>
          <span className="ev-stat-lbl">Answered</span>
        </div>
        <div className="ev-stat">
          <span className="ev-stat-val ev-stat-val--red">{unanswered}</span>
          <span className="ev-stat-lbl">Unanswered</span>
        </div>
        <div className="ev-stat ev-stat--score">
          <span className="ev-stat-val ev-stat-val--accent">{score}%</span>
          <span className="ev-stat-lbl">Score</span>
        </div>
      </div>
    </div>
  );
}

/* ─── Main workspace ─────────────────────────────────────────────────────── */
export default function EvaluationView() {
  const { sessionId } = useParams();
  const navigate = useNavigate();

  const [status, setStatus] = useState('pending');
  const [progressMsg, setProgressMsg] = useState('Queued…');
  const [result, setResult] = useState(null);
  const [pages, setPages] = useState([]);
  const [selectedQId, setSelectedQId] = useState(null);
  const [showUnmatched, setShowUnmatched] = useState(false);
  const [error, setError] = useState(null);
  const pollRef = useRef(null);

  /* ── Poll status until done ── */
  useEffect(() => {
    const poll = async () => {
      try {
        const s = await getEvaluationStatus(sessionId);
        setStatus(s.status);
        setProgressMsg(s.progress_message || '');

        if (s.status === 'done') {
          clearInterval(pollRef.current);
          const [mapping, pagesData] = await Promise.all([
            getEvaluationMapping(sessionId),
            getEvaluationPages(sessionId).catch(() => ({ pages: [] })),
          ]);
          setResult(mapping);
          setPages(pagesData.pages || []);
          if (mapping.mappings?.length > 0) {
            setSelectedQId(mapping.mappings[0].question.id);
          }
        } else if (s.status === 'error') {
          clearInterval(pollRef.current);
          setError(s.error || 'Processing failed.');
        }
      } catch {
        // ignore transient errors
      }
    };
    poll();
    pollRef.current = setInterval(poll, 2000);
    return () => clearInterval(pollRef.current);
  }, [sessionId]);

  /* ── Derived data ── */
  const selectedMapping = result?.mappings?.find((m) => m.question?.id === selectedQId);

  const highlightBlocks =
    selectedMapping?.answer_block?.blocks?.map((pb) => ({
      page: pb.page,
      ...pb.box,
    })) || [];

  const selectedVerdict = selectedMapping?.grade?.verdict
    || (selectedMapping?.mapping?.match_type === 'unanswered' ? 'unanswered' : 'incorrect');

  const selectedLabel = selectedMapping
    ? `Q${selectedMapping.question.number}${selectedMapping.question.sub_part ? `(${selectedMapping.question.sub_part})` : ''}`
    : '';

  /* ── Loading screen ── */
  if (status !== 'done' && status !== 'error') {
    return <ProcessingScreen message={progressMsg} />;
  }

  /* ── Error screen ── */
  if (status === 'error') {
    return <ErrorScreen error={error} onBack={() => navigate('/evaluate')} />;
  }

  /* ── Workspace ── */
  return (
    <div className="ev-workspace">
      {/* Top bar */}
      <TopBar
        onBack={() => navigate('/evaluate')}
        total={result.total_questions}
        answered={result.answered}
        unanswered={result.unanswered}
        score={result.score_percent}
      />

      <div className="ev-body">
        {/* ── Left panel ── */}
        <div className="ev-left">
          <div className="ev-left-header">
            <span>Extracted Questions</span>
            <span className="ev-left-sub">(from question paper)</span>
          </div>

          <div className="ev-question-list">
            {result.mappings?.map((m) => (
              <QuestionListItem
                key={m.question.id}
                mapping={m}
                selected={selectedQId === m.question.id}
                onSelect={() => setSelectedQId(m.question.id)}
              />
            ))}

            {/* Unmatched answers collapsible section */}
            {result.unmatched_answers?.length > 0 && (
              <div className="ev-unmatched-section">
                <button
                  className="ev-unmatched-toggle"
                  onClick={() => setShowUnmatched((v) => !v)}
                >
                  <span>Unmatched Answers ({result.unmatched_answers.length})</span>
                  <HiOutlineChevronDown
                    style={{ transform: showUnmatched ? 'rotate(180deg)' : 'none', transition: '200ms' }}
                  />
                </button>
                {showUnmatched && result.unmatched_answers.map((ab) => (
                  <div key={ab.id} className="ev-unmatched-item">
                    <span className="ev-unmatched-label">{ab.label || 'Unlabeled'}</span>
                    <span className="ev-unmatched-text">{ab.text?.slice(0, 120)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* ── Right panel ── */}
        <div className="ev-right">
          <div className="ev-right-header">
            <span>Answer Sheet</span>
            {selectedLabel && (
              <span className="ev-right-sub">
                Showing: <strong>{selectedLabel}</strong>
              </span>
            )}
          </div>

          {/* Answer sheet viewer */}
          <div className="ev-sheet-wrap">
            {pages.length > 0 ? (
              <AnswerSheetViewer
                pages={pages}
                highlightBlocks={highlightBlocks}
                verdict={selectedVerdict}
                questionLabel={selectedLabel}
              />
            ) : (
              <div className="ev-sheet-placeholder">
                Answer sheet images loading…
              </div>
            )}
          </div>

          {/* Detail panel */}
          {selectedMapping && (
            <div className="ev-detail">
              <div className="ev-detail-qtext">
                <strong>{selectedLabel}:</strong> {selectedMapping.question.text}
              </div>

              {selectedMapping.answer_block ? (
                <>
                  <div className="ev-detail-answer">
                    <div className="ev-detail-answer-label">
                      Student's Answer
                      {selectedMapping.answer_block.status === 'unlabeled_continuation' && (
                        <span className="ev-flag-chip">Unlabeled continuation</span>
                      )}
                    </div>
                    <div className="ev-detail-answer-text">
                      {selectedMapping.answer_block.text}
                    </div>
                  </div>

                  {selectedMapping.grade && (
                    <div className="ev-detail-feedback">
                      <div className="ev-detail-feedback-label">
                        <HiOutlineSparkles />
                        AI Feedback
                      </div>
                      <div className="ev-detail-feedback-text">
                        {selectedMapping.grade.feedback}
                      </div>
                      <div className="ev-detail-score">
                        Score: <strong>{(selectedMapping.grade.marks * 100).toFixed(0)}/100</strong>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="ev-detail-unanswered">
                  <HiOutlineExclamationCircle />
                  No answer found for this question
                </div>
              )}

              {/* Confidence flags */}
              {(selectedMapping.question.confidence === 'low' ||
                selectedMapping.mapping.match_type === 'matched_by_similarity') && (
                <div className="ev-flag-box">
                  <HiOutlineExclamationCircle />
                  <div>
                    {selectedMapping.question.confidence === 'low' && (
                      <div>⚠ Low OCR confidence — verify this question manually</div>
                    )}
                    {selectedMapping.mapping.match_type === 'matched_by_similarity' && (
                      <div>⚠ Matched via AI similarity, not exact label — verify the match</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Overall summary */}
          {result.overall_summary && (
            <div className="ev-summary">
              <div className="ev-summary-label">
                <HiOutlineSparkles />
                Overall Summary
              </div>
              <div className="ev-summary-text">
                {result.overall_summary.split('\n').map((line, i) =>
                  line.trim() ? <p key={i}>{line}</p> : <br key={i} />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
