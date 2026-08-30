import { NavLink, useLocation } from 'react-router-dom';
import { useState, useEffect } from 'react';
import { getHealth } from '../api/client';
import { HiOutlineHome, HiOutlineCloudUpload, HiOutlineDocumentText, HiOutlineChatAlt2, HiOutlineSparkles, HiOutlineAcademicCap } from 'react-icons/hi';

const navItems = [
  { path: '/', label: 'Dashboard', icon: <HiOutlineHome /> },
  { path: '/upload', label: 'Upload Documents', icon: <HiOutlineCloudUpload /> },
  { path: '/documents', label: 'My Documents', icon: <HiOutlineDocumentText /> },
  { path: '/query', label: 'Ask Questions', icon: <HiOutlineChatAlt2 /> },
  { path: '/summarize', label: 'Summarize', icon: <HiOutlineSparkles /> },
  { path: '/evaluate', label: 'Grade Answer Sheet', icon: <HiOutlineAcademicCap /> },
];

export default function Layout({ children }) {
  const location = useLocation();
  const [health, setHealth] = useState(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, [location.pathname]);

  return (
    <div className="app-layout">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <div className="sidebar-logo-icon">⚡</div>
            <div className="sidebar-logo-text">
              DocInsight
              <span>AI Document Analyzer</span>
            </div>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(({ path, label, icon }) => (
            <NavLink
              key={path}
              to={path}
              end={path === '/'}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-link-icon">{icon}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-stats">
            <div className="sidebar-stat">
              <span>Documents</span>
              <span className="sidebar-stat-value">{health?.document_count ?? '—'}</span>
            </div>
            <div className="sidebar-stat">
              <span>Vectors</span>
              <span className="sidebar-stat-value">{health?.index_size ?? '—'}</span>
            </div>
            <div className="sidebar-stat">
              <span>Tesseract</span>
              <span className="sidebar-stat-value">
                {health === null ? '—' : health.tesseract_available ? '✓' : '✗'}
              </span>
            </div>
            <div className="sidebar-stat">
              <span>OpenAI</span>
              <span className="sidebar-stat-value">
                {health === null ? '—' : health.openai_configured ? '✓' : '✗'}
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="main-content">
        {children}
      </main>
    </div>
  );
}
