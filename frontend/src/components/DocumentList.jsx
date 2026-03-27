import { useEffect, useState } from 'react';
import { listDocuments, deleteDocument } from '../api/client';
import { HiOutlineDocumentText, HiOutlineTrash, HiOutlineSearch, HiOutlineRefresh } from 'react-icons/hi';

const fileTypeIcon = (type) => {
  if (type === 'pdf') return 'file-icon-pdf';
  if (['png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'webp'].includes(type)) return 'file-icon-image';
  return 'file-icon-text';
};

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
};

export default function DocumentList() {
  const [docs, setDocs] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState(null);

  const fetchDocs = () => {
    setLoading(true);
    listDocuments()
      .then((data) => setDocs(data.documents || []))
      .catch(() => setDocs([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchDocs(); }, []);

  const handleDelete = async (id) => {
    if (!confirm('Delete this document and all its indexed data?')) return;
    setDeleting(id);
    try {
      await deleteDocument(id);
      setDocs((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      alert('Failed to delete: ' + (err.response?.data?.detail || err.message));
    }
    setDeleting(null);
  };

  const filtered = docs.filter((d) =>
    d.filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">My Documents</h1>
        <p className="page-subtitle">Manage your uploaded and indexed documents</p>
      </div>

      <div className="page-content">
        {/* Toolbar */}
        <div style={{ display: 'flex', gap: 'var(--space-3)', marginBottom: 'var(--space-6)', alignItems: 'center' }}>
          <div style={{ position: 'relative', flex: 1, maxWidth: 400 }}>
            <HiOutlineSearch style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
            <input
              className="input"
              placeholder="Search documents…"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{ paddingLeft: 36 }}
            />
          </div>
          <button className="btn btn-secondary" onClick={fetchDocs}>
            <HiOutlineRefresh /> Refresh
          </button>
        </div>

        {/* Table */}
        {loading ? (
          <div className="empty-state">
            <div className="spinner spinner-lg" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="empty-state">
            <div className="empty-state-icon"><HiOutlineDocumentText /></div>
            <div className="empty-state-title">
              {search ? 'No documents match your search' : 'No documents uploaded yet'}
            </div>
            <div className="empty-state-text">
              {search ? 'Try a different search term.' : 'Upload PDFs, images, or text files to get started.'}
            </div>
          </div>
        ) : (
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <table className="doc-table">
              <thead>
                <tr>
                  <th>Document</th>
                  <th>Type</th>
                  <th>Size</th>
                  <th>Pages</th>
                  <th>Chunks</th>
                  <th>Status</th>
                  <th>Language</th>
                  <th style={{ width: 60 }}></th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <div className="doc-name">
                        <div className={`doc-name-icon ${fileTypeIcon(doc.file_type)}`}>
                          <HiOutlineDocumentText />
                        </div>
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 250 }}>
                          {doc.filename}
                        </span>
                      </div>
                    </td>
                    <td><span className="badge badge-accent">{doc.file_type.toUpperCase()}</span></td>
                    <td style={{ color: 'var(--color-text-secondary)', fontSize: 'var(--font-size-sm)' }}>{formatBytes(doc.file_size)}</td>
                    <td style={{ color: 'var(--color-text-secondary)' }}>{doc.page_count}</td>
                    <td style={{ color: 'var(--color-text-secondary)' }}>{doc.chunk_count}</td>
                    <td>
                      <span className={`badge ${doc.status === 'ready' ? 'badge-success' : doc.status === 'error' ? 'badge-error' : 'badge-warning'}`}>
                        {doc.status}
                      </span>
                    </td>
                    <td style={{ color: 'var(--color-text-muted)', fontSize: 'var(--font-size-sm)' }}>{doc.language}</td>
                    <td>
                      <button
                        className="btn btn-ghost btn-sm"
                        onClick={() => handleDelete(doc.id)}
                        disabled={deleting === doc.id}
                        title="Delete document"
                        style={{ color: 'var(--color-error)' }}
                      >
                        {deleting === doc.id ? <div className="spinner" /> : <HiOutlineTrash />}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!loading && (
          <div style={{ marginTop: 'var(--space-4)', fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)' }}>
            {filtered.length} of {docs.length} document{docs.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>
    </>
  );
}
