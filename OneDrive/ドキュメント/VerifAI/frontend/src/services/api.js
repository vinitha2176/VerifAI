import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Accept': 'application/json',
  },
});

/**
 * Handle API error messages consistently
 */
export const formatApiError = (error) => {
  if (error.response) {
    const data = error.response.data;
    if (data?.detail) {
      if (Array.isArray(data.detail)) {
        return data.detail.map((err) => err.msg || JSON.stringify(err)).join(', ');
      }
      return String(data.detail);
    }
    return `Server returned error (${error.response.status})`;
  } else if (error.request) {
    return 'Unable to connect to the VerifAI backend server. Please verify the backend is running on port 8000.';
  }
  return error.message || 'An unexpected error occurred.';
};

/**
 * Analyze plain text recruitment notice or offer email
 * @param {string} text - Recruitment text content
 */
export const analyzeText = async (text) => {
  try {
    const response = await apiClient.post('/api/analyze/text', { text });
    return response.data;
  } catch (error) {
    throw new Error(formatApiError(error));
  }
};

/**
 * Upload and analyze PDF recruitment document
 * @param {File} file - PDF file object
 */
export const analyzeFile = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/api/analyze/file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  } catch (error) {
    throw new Error(formatApiError(error));
  }
};

/**
 * Fetch paginated analysis history
 * @param {number} limit
 * @param {number} offset
 */
export const getHistory = async (limit = 20, offset = 0) => {
  try {
    const response = await apiClient.get('/api/history', {
      params: { limit, offset },
    });
    return response.data;
  } catch (error) {
    throw new Error(formatApiError(error));
  }
};

/**
 * Fetch detailed analysis record by ID
 * @param {number|string} id
 */
export const getAnalysisDetail = async (id) => {
  try {
    const response = await apiClient.get(`/api/history/${id}`);
    return response.data;
  } catch (error) {
    throw new Error(formatApiError(error));
  }
};

/**
 * Delete an analysis record by ID
 * @param {number|string} id
 */
export const deleteAnalysis = async (id) => {
  try {
    const response = await apiClient.delete(`/api/history/${id}`);
    return response.data;
  } catch (error) {
    throw new Error(formatApiError(error));
  }
};

/**
 * Fetch trained ML model performance metrics
 */
export const getModelMetrics = async () => {
  try {
    const response = await apiClient.get('/api/model/metrics');
    return response.data;
  } catch (error) {
    throw new Error(formatApiError(error));
  }
};

/**
 * Fetch system health and component connectivity
 */
export const getHealth = async () => {
  try {
    const response = await apiClient.get('/api/health');
    return response.data;
  } catch (error) {
    throw new Error(formatApiError(error));
  }
};

export default apiClient;

