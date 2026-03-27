import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getHealth, listDocuments } from '../api/client';
import { HiOutlineCloudUpload, HiOutlineChatAlt2, HiOutlineSparkles, HiOutlineDocumentText, HiOutlineDatabase, HiOutlineGlobe, HiOutlineLightningBolt } from 'react-icons/hi';

export default function Dashboard() {
  const navigate = useNavigate();
  const [health, setHealth] = useState(null);
  const [recentDocs, setRecentDocs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getHealth().catch(() => null),
      listDocuments().catch(() => ({ documents: [], total: 0 })),
    ]).then(([h, docs]) => {
      setHealth(h);
      setRecentDocs(docs.documents.slice(-5).reverse());
      setLoading(false);
    });
  }, []);

  const stats = [
    {
      label: 'Total Documents',
      value: health?.document_count ?? 0,
      icon: <HiOutlineDocumentText />,
      color: 'purple',
    },
    {
      label: 'Index Vectors',
      value: health?.index_size ?? 0,
      icon: <HiOutlineDatabase />,
      color: 'blue',
    },
    {
      label: 'OCR Engine',
      value: health?.tesseract_available ? 'Active' : 'Offline',
      icon: <HiOutlineGlobe />,
      color: 'green',
    },
    {
      label: 'AI Engine',
      value: health?.openai_configured ? 'Connected' : 'Not Set',
      icon: <HiOutlineLightningBolt />,
      color: 'orange',
    },
  ];

  const actions = [
    {
      title: 'Upload Documents',
      desc: 'Upload PDFs, images, or text files for OCR processing and indexing.',
      icon: <HiOutlineCloudUpload />,
      path: '/upload',
    },
    {
      title: 'Ask Questions',
      desc: 'Query your documents using AI-powered RAG for instant answers with sources.',
      icon: <HiOutlineChatAlt2 />,
      path: '/query',
    },
    {
      title: 'Generate Summaries',
      desc: 'Create concise summaries of one or more documents with key insights.',
      icon: <HiOutlineSparkles />,
      path: '/summarize',
    },
  ];

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">Overview of your document intelligence platform</p>
      </div>

      <div className="page-content">
        {/* Stats */}
        <div className="dashboard-grid">
          {stats.map((s) => (
            <div key={s.label} className="card card-glass">
              <div className="stat-card">
                <div className={`stat-icon ${s.color}`}>{s.icon}</div>
                <div>
                  <div className="stat-value">{loading ? '—' : s.value}</div>
                  <div className="stat-label">{s.label}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Quick actions */}
        <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-4)' }}>
          Quick Actions
        </h2>
        <div className="dashboard-actions">
          {actions.map((a) => (
            <div key={a.title} className="card action-card" onClick={() => navigate(a.path)}>
              <div className="action-card-icon">{a.icon}</div>
              <div className="action-card-title">{a.title}</div>
              <div className="action-card-desc">{a.desc}</div>
            </div>
          ))}
        </div>

        {/* Recent documents */}
        {recentDocs.length > 0 && (
          <div style={{ marginTop: 'var(--space-8)' }}>
            <h2 style={{ fontSize: 'var(--font-size-lg)', fontWeight: 'var(--font-weight-semibold)', marginBottom: 'var(--space-4)' }}>
              Recent Documents
            </h2>
            <div className="card">
              <table className="doc-table">
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Type</th>
                    <th>Status</th>
                    <th>Chunks</th>
                  </tr>
                </thead>
                <tbody>
                  {recentDocs.map((doc) => (
                    <tr key={doc.id}>
                      <td>
                        <div className="doc-name">
                          <div className="doc-name-icon">
                            <HiOutlineDocumentText />
                          </div>
                          {doc.filename}
                        </div>
                      </td>
                      <td><span className="badge badge-accent">{doc.file_type}</span></td>
                      <td>
                        <span className={`badge ${doc.status === 'ready' ? 'badge-success' : doc.status === 'error' ? 'badge-error' : 'badge-warning'}`}>
                          {doc.status}
                        </span>
                      </td>
                      <td style={{ color: 'var(--color-text-secondary)' }}>{doc.chunk_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </>
  );
}
