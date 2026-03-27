import { useState, useEffect } from 'react';
import { listDocuments, summarizeDocuments } from '../api/client';
import { HiOutlineSparkles, HiOutlineDocumentText } from 'react-icons/hi';

export default function SummaryView() {
  const [docs, setDocs] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [docsLoading, setDocsLoading] = useState(true);

  useEffect(() => {
    listDocuments()
      .then((data) => setDocs(data.documents?.filter((d) => d.status === 'ready') || []))
      .catch(() => setDocs([]))
      .finally(() => setDocsLoading(false));
  }, []);

  const toggleDoc = (id) => {
    setSelectedDocs((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const handleSummarize = async () => {
    if (selectedDocs.length === 0) return;
    setLoading(true);
    setError(null);
    setSummary(null);

    try {
      const result = await summarizeDocuments(selectedDocs);
      setSummary(result);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
    setLoading(false);
  };

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Summarize Documents</h1>
        <p className="page-subtitle">Generate AI-powered summaries of your uploaded documents</p>
      </div>

      <div className="page-content">
        {/* Document selector */}
        <div className="card" style={{ marginBottom: 'var(--space-6)' }}>
          <div className="card-header">
            <h3 className="card-title">Select Documents to Summarize</h3>
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
              {selectedDocs.length} selected
            </span>
          </div>

          {docsLoading ? (
            <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-8)' }}>
              <div className="spinner" />
            </div>
          ) : docs.length === 0 ? (
            <div className="empty-state" style={{ padding: 'var(--space-8)' }}>
              <div className="empty-state-icon" style={{ fontSize: '2.5rem' }}><HiOutlineDocumentText /></div>
              <div className="empty-state-title">No documents available</div>
              <div className="empty-state-text">Upload and index documents first to generate summaries.</div>
            </div>
          ) : (
            <>
              <div className="doc-selector">
                {docs.map((d) => (
                  <button
                    key={d.id}
                    className={`doc-chip ${selectedDocs.includes(d.id) ? 'selected' : ''}`}
                    onClick={() => toggleDoc(d.id)}
                  >
                    <HiOutlineDocumentText />
                    <span style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {d.filename}
                    </span>
                    <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                      ({d.chunk_count} chunks)
                    </span>
                  </button>
                ))}
              </div>

              <div style={{ marginTop: 'var(--space-4)', display: 'flex', gap: 'var(--space-3)' }}>
                <button
                  className="btn btn-primary"
                  onClick={handleSummarize}
                  disabled={selectedDocs.length === 0 || loading}
                >
                  {loading ? (
                    <>
                      <div className="spinner" style={{ borderTopColor: 'white' }} />
                      Generating…
                    </>
                  ) : (
                    <>
                      <HiOutlineSparkles />
                      Generate Summary
                    </>
                  )}
                </button>

                {selectedDocs.length > 0 && (
                  <button
                    className="btn btn-secondary"
                    onClick={() => setSelectedDocs([])}
                  >
                    Clear Selection
                  </button>
                )}
              </div>
            </>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="card" style={{ borderColor: 'rgba(239, 68, 68, 0.3)', marginBottom: 'var(--space-6)' }}>
            <div style={{ color: 'var(--color-error)', fontWeight: 'var(--font-weight-medium)', marginBottom: 'var(--space-2)' }}>
              Error
            </div>
            <div style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>
              {error}
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="card" style={{ textAlign: 'center', padding: 'var(--space-12)' }}>
            <div className="spinner spinner-lg" style={{ margin: '0 auto var(--space-4)' }} />
            <div style={{ fontSize: 'var(--font-size-md)', fontWeight: 'var(--font-weight-medium)', color: 'var(--color-text-primary)' }}>
              Generating Summary…
            </div>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginTop: 'var(--space-2)' }}>
              Analyzing document content with AI. This may take a moment.
            </div>
          </div>
        )}

        {/* Summary result */}
        {summary && !loading && (
          <div className="card">
            <div className="card-header">
              <h3 className="card-title" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                <HiOutlineSparkles style={{ color: 'var(--color-accent)' }} />
                Generated Summary
              </h3>
              <span className="badge badge-info">{summary.model}</span>
            </div>
            <div className="summary-content">
              {summary.summary.split('\n').map((line, i) => {
                if (!line.trim()) return <br key={i} />;
                if (line.startsWith('# ')) return <h1 key={i}>{line.slice(2)}</h1>;
                if (line.startsWith('## ')) return <h2 key={i}>{line.slice(3)}</h2>;
                if (line.startsWith('### ')) return <h3 key={i}>{line.slice(4)}</h3>;
                if (line.match(/^\d+\.\s/)) return <p key={i} style={{ paddingLeft: 'var(--space-4)' }}>{line}</p>;
                if (line.startsWith('- ')) return <p key={i} style={{ paddingLeft: 'var(--space-4)' }}>• {line.slice(2)}</p>;
                return <p key={i}>{line}</p>;
              })}
            </div>
          </div>
        )}
      </div>
    </>
  );
}
