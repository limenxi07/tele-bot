import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Extract token from URL
export const getTokenFromUrl = () => {
  const params = new URLSearchParams(window.location.search);
  return params.get('token');
};

// Store user_id in sessionStorage after token validation
export const setUserId = (userId) => {
  sessionStorage.setItem('user_id', userId);
};

export const getUserId = () => {
  return sessionStorage.getItem('user_id');
};

// Set up axios interceptor to add Authorization header
api.interceptors.request.use((config) => {
  const userId = getUserId();
  if (userId) {
    config.headers.Authorization = `Bearer ${userId}`;
  }
  return config;
});
