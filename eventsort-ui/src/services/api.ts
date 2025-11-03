import axios from 'axios';
import { Event, AuthResponse, SwipeResponse, Stats } from '../types/Event';

const API_BASE_URL = 'https://api-production-ce2b.up.railway.app/';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to all requests
api.interceptors.request.use((config) => {
  const userId = localStorage.getItem('user_id');
  if (userId) {
    config.headers.Authorization = `Bearer ${userId}`;
  }
  return config;
});

// API functions
export const validateToken = async (token: string): Promise<AuthResponse> => {
  const response = await axios.post(`${API_BASE_URL}/auth/validate-token`, null, {
    params: { token }
  });
  return response.data;
};

export const getEvents = async (filter: 'all' | 'upcoming' | 'urgent' = 'upcoming'): Promise<Event[]> => {
  const response = await api.get('/events', {
    params: { filter, include_raw: false }
  });
  return response.data;
};

export const getEvent = async (eventId: number, includeRaw: boolean = true): Promise<Event> => {
  const response = await api.get(`/events/${eventId}`, {
    params: { include_raw: includeRaw }
  });
  return response.data;
};

export const swipeEvent = async (eventId: number, interested: boolean): Promise<SwipeResponse> => {
  const response = await api.post(`/events/${eventId}/swipe`, { interested });
  return response.data;
};

export const getInterestedEvents = async (): Promise<Event[]> => {
  const response = await api.get('/events/interested/all', {
    params: { include_raw: false }
  });
  return response.data;
};

export const getStats = async (): Promise<Stats> => {
  const response = await api.get('/stats');
  return response.data;
};