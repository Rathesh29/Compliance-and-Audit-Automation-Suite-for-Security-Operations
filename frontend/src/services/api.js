import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request interceptor: attach Bearer token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: extract envelope data & handle auth expiration
api.interceptors.response.use(
  (response) => {
    // If blob (e.g. PDF/CSV export), return directly
    if (response.config.responseType === 'blob') {
      return response;
    }
    // Unwrap standard envelope { success: true, data: ... }
    if (response.data && response.data.success !== undefined) {
      return response.data.data;
    }
    return response.data;
  },
  (error) => {
    if (error.response) {
      const status = error.response.status;
      if (status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      const errData = error.response.data?.error || error.response.data;
      return Promise.reject(errData || new Error(error.response.statusText));
    }
    return Promise.reject(new Error('Network error. Backend service may be unreachable.'));
  }
);

export default api;
