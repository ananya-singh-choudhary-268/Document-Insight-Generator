import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadEvaluation } from '../api/evaluationClient';
import {
  HiOutlineDocumentText,
  HiOutlineAcademicCap,
  HiOutlineX,
  HiOutlineExclamationCircle,
  HiOutlineArrowRight,
  HiOutlinePaperClip,
} from 'react-icons/hi';

/* ── File slot ──────────────────────────────────────────────────────────── */
function FileSlot({ label, sublabel, icon, file, onFile, onRemove, disabled }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f && !disabled) onFile(f);
  };

  if (file) {
    return (
      <div className="eu-slot eu-slot--filled">
        <div className="eu-slot-check">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <circle cx="10" cy="10" r="10" fill="var(--color-success)" opacity=".15"/>
            <path d="M6 10l3 3 5-5" stroke="var(--color-success)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
        <div className="eu-slot-info">
          <div className="eu-slot-label">{label}</div>
          <div className="eu-slot-filename">
            <HiOutlinePaperClip style={{ flexShrink: 0 }}/>
            <span>{file.name}</span>
            <span className="eu-slot-size">({(file.size / 1024).toFixed(0)} KB)</span>
          </div>
        </div>
        <button
          className="eu-slot-remove"
          onClick={(e) => { e.stopPropagation(); onRemove(); }}
          title="Remove file"
        >
          <HiOutlineX />
        </button>
      </div>
    );
  }

  return (
    <div
      className={`eu-slot eu-slot--empty ${dragging ? 'dragging' : ''}`}
      onDrop={onDrop}
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onClick={() => !disabled && inputRef.current?.click()}
      style={{ cursor: disabled ? 'not-allowed' : 'pointer' }}
    >
      <input
        ref={inputRef}
        type="file"
        style={{ display: 'none' }}
        accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif,.bmp,.webp"
        onChange={(e) => { if (e.target.files[0]) onFile(e.target.files[0]); }}
        disabled={disabled}
      />
      <div className="eu-slot-icon">{icon}</div>
      <div className="eu-slot-info">
        <div className="eu-slot-label">{label}</div>
        <div className="eu-slot-sub">{sublabel}</div>
      </div>
      <div className="eu-slot-cta">Browse</div>
    </div>
  );
}

/* ── Main upload page ───────────────────────────────────────────────────── */
export default function EvaluationUpload() {
  const navigate = useNavigate();
  const [questionPaper, setQuestionPaper] = useState(null);
  const [answerSheet, setAnswerSheet] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  const canSubmit = questionPaper && answerSheet && !uploading;

  const handleSubmit = async () => {
    if (!canSubmit) return;
    setUploading(true);
    setError(null);
    try {
      const result = await uploadEvaluation(questionPaper, answerSheet);
      navigate(`/evaluate/${result.session_id}`);
    } catch (err) {
      setUploading(false);
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <div className="eu-page">
      <div className="eu-card">
        {/* Header */}
        <div className="eu-card-header">
          <div className="eu-card-icon">
            <HiOutlineAcademicCap />
          </div>
          <div>
            <h1 className="eu-card-title">Upload Question Paper &amp; Answer Sheets</h1>
            <p className="eu-card-sub">Supports PDF and image files (PNG, JPG, TIFF, WEBP)</p>
          </div>
        </div>

        {/* Two upload slots */}
        <div className="eu-slots">
          <FileSlot
            label="Upload Question Paper"
            sublabel="The printed question paper (PDF or image)"
            icon={<HiOutlineDocumentText />}
            file={questionPaper}
            onFile={setQuestionPaper}
            onRemove={() => setQuestionPaper(null)}
            disabled={uploading}
          />
          <FileSlot
            label="Upload Answer Sheets"
            sublabel="The student's handwritten answers (PDF or image)"
            icon={<HiOutlineAcademicCap />}
            file={answerSheet}
            onFile={setAnswerSheet}
            onRemove={() => setAnswerSheet(null)}
            disabled={uploading}
          />
        </div>

        {/* Error */}
        {error && (
          <div className="eu-error">
            <HiOutlineExclamationCircle />
            <span>{error}</span>
          </div>
        )}

        {/* Submit */}
        <button
          className={`eu-submit ${canSubmit ? 'active' : ''}`}
          onClick={handleSubmit}
          disabled={!canSubmit}
          id="eval-submit-btn"
        >
          {uploading ? (
            <>
              <span className="eu-spinner" />
              Uploading…
            </>
          ) : (
            <>
              Get Started
              <HiOutlineArrowRight />
            </>
          )}
        </button>
      </div>
    </div>
  );
}
