import axios from 'axios';

// API Base URL - explicitly set for development
// In production, set REACT_APP_API_URL environment variable
const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json',
    },
});

// ==================== Stats ====================
export const getStats = async () => {
    const response = await api.get('/stats');
    return response.data;
};

// ==================== Users ====================
export const createUser = async (userData) => {
    const response = await api.post('/users', userData);
    return response.data;
};

export const getUser = async (userId) => {
    const response = await api.get(`/users/${userId}`);
    return response.data;
};

// ==================== Reports ====================
export const getReports = async (params = {}) => {
    const response = await api.get('/reports', { params });
    return response.data;
};

export const getReport = async (reportId) => {
    const response = await api.get(`/reports/${reportId}`);
    return response.data;
};

export const submitReport = async (reportData) => {
    const response = await api.post('/reports', reportData);
    return response.data;
};

// ==================== Health ====================
export const healthCheck = async () => {
    const response = await api.get('/health');
    return response.data;
};

export default api;
