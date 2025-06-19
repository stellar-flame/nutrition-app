import axios from 'axios';

const api = axios.create({
  baseURL: process.env.EXPO_PUBLIC_API_BASE_URL || 'http://192.168.0.9:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
