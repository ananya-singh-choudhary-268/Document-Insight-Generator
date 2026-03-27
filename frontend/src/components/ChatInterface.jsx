import { useState, useRef, useEffect } from 'react';
import { queryDocuments, listDocuments } from '../api/client';
import { HiOutlinePaperAirplane, HiOutlineDocumentText } from 'react-icons/hi';

export default function ChatInterface() {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      content: 'Hello! I\'m your document analysis assistant. Upload some documents and ask me anything about them. I\'ll search through your indexed documents to find relevant answers.',
      sources: [],
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [docs, setDocs] = useState([]);
  const [selectedDocs, setSelectedDocs] = useState([]);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    listDocuments()
      .then((data) => setDocs(data.documents?.filter((d) => d.status === 'ready') || []))
      .catch(() => {});
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const toggleDoc = (id) => {
    setSelectedDocs((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]
    );
  };

  const handleSend = async () => {
    const question = input.trim();
    if (!question || loading) return;

    const userMsg = { role: 'user', content: question, sources: [] };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const result = await queryDocuments(
        question,
        selectedDocs.length > 0 ? selectedDocs : null
      );
      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          content: result.answer,
          sources: result.sources || [],
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'ai',
          content: `Sorry, an error occurred: ${err.response?.data?.detail || err.message}`,
          sources: [],
        },
      ]);
    }

    setLoading(false);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <div className="page-header">
        <h1 className="page-title">Ask Questions</h1>
        <p className="page-subtitle">Query your documents using AI-powered retrieval-augmented generation</p>
      </div>

      <div className="page-content">
        {/* Document filter */}
        {docs.length > 0 && (
          <div style={{ marginBottom: 'var(--space-4)' }}>
            <div style={{ fontSize: 'var(--font-size-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-2)' }}>
              Filter by document (optional):
            </div>
            <div className="doc-selector">
              {docs.map((d) => (
                <button
                  key={d.id}
                  className={`doc-chip ${selectedDocs.includes(d.id) ? 'selected' : ''}`}
                  onClick={() => toggleDoc(d.id)}
                >
                  <HiOutlineDocumentText />
                  <span style={{ maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {d.filename}
                  </span>
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Chat area */}
        <div className="card chat-container" style={{ padding: 0 }}>
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.role === 'user' ? 'user' : 'ai'}`}>
                <div className={`chat-avatar ${msg.role}`}>
                  {msg.role === 'ai' ? '🤖' : '👤'}
                </div>
                <div>
                  <div className="chat-bubble">{msg.content}</div>
                  {msg.sources?.length > 0 && (
                    <div className="chat-sources">
                      <div style={{ fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-2)' }}>
                        Sources:
                      </div>
                      {msg.sources.map((s, j) => (
                        <span key={j} className="chat-source-tag">
                          <HiOutlineDocumentText />
                          {s.document_name} (chunk {s.chunk_index + 1})
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {loading && (
              <div className="chat-message ai">
                <div className="chat-avatar ai">🤖</div>
                <div className="chat-bubble">
                  <div className="loading-dots">
                    <span></span><span></span><span></span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-area">
            <input
              ref={inputRef}
              className="input"
              placeholder="Ask a question about your documents…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={loading}
            />
            <button
              className="btn btn-primary"
              onClick={handleSend}
              disabled={!input.trim() || loading}
            >
              <HiOutlinePaperAirplane style={{ transform: 'rotate(90deg)' }} />
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
