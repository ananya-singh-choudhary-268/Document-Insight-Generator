/**
 * API client — Axios wrapper for the FastAPI backend.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for long OCR/LLM calls
  headers: {
    'Accept': 'application/json',
  },
});

// ── Documents ──────────────────────────────────────────────────────────

export async function uploadDocument(file, language = null) {
  const formData = new FormData();
  formData.append('file', file);
  if (language) formData.append('language', language);

  const response = await api.post('/documents/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function listDocuments() {
  const response = await api.get('/documents');
  return response.data;
}

export async function getDocument(docId) {
  const response = await api.get(`/documents/${docId}`);
  return response.data;
}

export async function deleteDocument(docId) {
  const response = await api.delete(`/documents/${docId}`);
  return response.data;
}

// ── Query ──────────────────────────────────────────────────────────────

export async function queryDocuments(question, documentIds = null) {
  const response = await api.post('/query', {
    question,
    document_ids: documentIds,
  });
  return response.data;
}

// ── Summarize ──────────────────────────────────────────────────────────

export async function summarizeDocuments(documentIds) {
  const response = await api.post('/summarize', {
    document_ids: documentIds,
  });
  return response.data;
}

// ── Health ──────────────────────────────────────────────────────────────

export async function getHealth() {
  const response = await api.get('/health');
  return response.data;
}

export default api;
