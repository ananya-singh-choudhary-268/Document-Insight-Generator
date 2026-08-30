/**
 * Evaluation API client methods — additive to existing client.js.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 300000, // 5 min for large grading jobs
  headers: { Accept: 'application/json' },
});

export async function uploadEvaluation(questionPaperFile, answerSheetFile, onProgress) {
  const formData = new FormData();
  formData.append('question_paper', questionPaperFile);
  formData.append('answer_sheet', answerSheetFile);

  const response = await api.post('/evaluation/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    },
  });
  return response.data; // { session_id, message }
}

export async function getEvaluationStatus(sessionId) {
  const response = await api.get(`/evaluation/${sessionId}/status`);
  return response.data;
}

export async function getEvaluationQuestions(sessionId) {
  const response = await api.get(`/evaluation/${sessionId}/questions`);
  return response.data;
}

export async function getEvaluationPages(sessionId) {
  const response = await api.get(`/evaluation/${sessionId}/pages`);
  return response.data; // { pages: [{page, b64}] }
}

export async function getEvaluationMapping(sessionId) {
  const response = await api.get(`/evaluation/${sessionId}/mapping`);
  return response.data;
}

export default api;
