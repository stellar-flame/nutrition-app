import axios from 'axios';

const api = axios.create({
  baseURL: 'https://rwcr3l3bz8.execute-api.us-east-1.amazonaws.com/prod',
  // baseURL: 'http://192.168.0.9:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
