import { useState, useRef } from 'react';
import { uploadDocument } from '../api/client';
import { HiOutlineCloudUpload, HiOutlineDocumentText, HiOutlineCheckCircle, HiOutlineExclamationCircle } from 'react-icons/hi';

const SUPPORTED = ['PDF', 'PNG', 'JPG', 'JPEG', 'TIFF', 'TIF', 'BMP', 'WEBP', 'TXT', 'MD', 'CSV', 'JSON'];
const LANGUAGE_OPTIONS = [
  { value: 'eng', label: 'English' },
  { value: 'fra', label: 'French' },
  { value: 'deu', label: 'German' },
  { value: 'spa', label: 'Spanish' },
  { value: 'ita', label: 'Italian' },
  { value: 'por', label: 'Portuguese' },
  { value: 'hin', label: 'Hindi' },
  { value: 'jpn', label: 'Japanese' },
  { value: 'kor', label: 'Korean' },
  { value: 'chi_sim', label: 'Chinese (Simplified)' },
  { value: 'ara', label: 'Arabic' },
  { value: 'rus', label: 'Russian' },
];

export default function DocumentUpload() {
  const [dragging, setDragging] = useState(false);
  const [language, setLanguage] = useState('eng');
  const [uploads, setUploads] = useState([]); // { file, status: 'uploading'|'success'|'error', result?, error? }
  const inputRef = useRef(null);

  const handleFiles = async (files) => {
    const fileArray = Array.from(files);

    for (const file of fileArray) {
      const entry = { file, status: 'uploading', result: null, error: null };
      setUploads((prev) => [entry, ...prev]);

      try {
        const result = await uploadDocument(file, language);
        setUploads((prev) =>
          prev.map((u) =>
            u.file === file ? { ...u, status: 'success', result } : u
          )
        );
      } catch (err) {
        setUploads((prev) =>
          prev.map((u) =>
            u.file === file
              ? { ...u, status: 'error', error: err.response?.data?.detail || err.message }
              : u
          )
        );
      }
    }
  };

  const onDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFiles(e.dataTransfer.files);
  };

  const onDragOver = (e) => {
    e.preventDefault();
    setDragging(true);
  };

  const onDragLeave = () => setDragging(false);

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Upload Documents</h1>
        <p className="page-subtitle">Upload PDFs, images, or text files for OCR processing and AI indexing</p>
      </div>

      <div className="page-content">
        {/* Language selector */}
        <div style={{ marginBottom: 'var(--space-6)', maxWidth: 300 }}>
          <label style={{ display: 'block', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-secondary)', marginBottom: 'var(--space-2)' }}>
            OCR Language
          </label>
          <select
            className="input"
            value={language}
            onChange={(e) => setLanguage(e.target.value)}
          >
            {LANGUAGE_OPTIONS.map((l) => (
              <option key={l.value} value={l.value}>{l.label}</option>
            ))}
          </select>
        </div>

        {/* Drop zone */}
        <div
          className={`upload-zone ${dragging ? 'dragging' : ''}`}
          onDrop={onDrop}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            multiple
            style={{ display: 'none' }}
            accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif,.bmp,.webp,.txt,.md,.csv,.json"
            onChange={(e) => handleFiles(e.target.files)}
          />
          <div className="upload-zone-content">
            <div className="upload-icon"><HiOutlineCloudUpload /></div>
            <div className="upload-title">Drop files here or click to browse</div>
            <div className="upload-subtitle">Supports multiple file uploads with multilingual OCR</div>
            <div className="upload-formats">
              {SUPPORTED.map((fmt) => (
                <span key={fmt} className="badge badge-accent">{fmt}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Upload results */}
        {uploads.length > 0 && (
          <div style={{ marginTop: 'var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <h3 style={{ fontSize: 'var(--font-size-md)', fontWeight: 'var(--font-weight-semibold)' }}>
              Upload History
            </h3>
            {uploads.map((u, i) => (
              <div key={i} className="card" style={{ padding: 'var(--space-4)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                  {u.status === 'uploading' && <div className="spinner" />}
                  {u.status === 'success' && <HiOutlineCheckCircle style={{ color: 'var(--color-success)', fontSize: '1.4rem' }} />}
                  {u.status === 'error' && <HiOutlineExclamationCircle style={{ color: 'var(--color-error)', fontSize: '1.4rem' }} />}

                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 'var(--font-weight-medium)', fontSize: 'var(--font-size-base)' }}>
                      {u.file.name}
                    </div>
                    <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginTop: 2 }}>
                      {u.status === 'uploading' && 'Processing with OCR…'}
                      {u.status === 'success' && `Ready — ${u.result.chunk_count} chunks indexed, ${u.result.page_count} page(s)`}
                      {u.status === 'error' && u.error}
                    </div>
                  </div>

                  {u.status === 'success' && (
                    <span className="badge badge-success">Ready</span>
                  )}
                  {u.status === 'error' && (
                    <span className="badge badge-error">Failed</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  );
}
