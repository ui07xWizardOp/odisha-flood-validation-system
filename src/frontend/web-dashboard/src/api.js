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

// ==================== Auth Token Management ====================
let authToken = localStorage.getItem('authToken');

api.interceptors.request.use((config) => {
    if (authToken) {
        config.headers.Authorization = `Bearer ${authToken}`;
    }
    return config;
});

export const setAuthToken = (token) => {
    authToken = token;
    if (token) {
        localStorage.setItem('authToken', token);
    } else {
        localStorage.removeItem('authToken');
    }
};

// ==================== Authentication ====================
export const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    if (response.data.access_token) {
        setAuthToken(response.data.access_token);
    }
    return response.data;
};

export const register = async (username, password, email = null) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    if (email) params.append('email', email);

    const response = await api.post('/auth/register', null, { params });
    return response.data;
};

export const logout = () => {
    setAuthToken(null);
};

export const getCurrentUser = async () => {
    const response = await api.get('/auth/me');
    return response.data;
};

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

export const getNearbyReports = async (lat, lon, radiusMeters = 1000) => {
    const response = await api.get('/reports/nearby', {
        params: { lat, lon, radius_m: radiusMeters }
    });
    return response.data;
};

// ==================== Photo Validation ====================
export const validatePhoto = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/validate-photo', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const submitImageReport = async (file, data) => {
    const formData = new FormData();
    formData.append('file', file);
    Object.keys(data).forEach(key => {
        formData.append(key, data[key]);
    });

    const response = await api.post('/reports/from-image', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

// ==================== Health ====================
export const healthCheck = async () => {
    const response = await api.get('/health');
    return response.data;
};

// ==================== Export Data ====================
export const exportReportsCSV = async () => {
    const response = await api.get('/export/csv', { responseType: 'blob' });
    return response.data;
};

export const exportReportsGeoJSON = async () => {
    const response = await api.get('/export/geojson');
    return response.data;
};

export default api;

