// src/services/api.js
// Single API client — all components import from here

import axios from 'axios'

// VITE_API_URL is set in Vercel environment variables.
// Fallback to Render URL for production if env var missing.
const BASE = import.meta.env.VITE_API_URL
  || (typeof window !== 'undefined' && window.location.hostname !== 'localhost'
      ? 'https://delhi-grid-intelligence.onrender.com'
      : 'http://localhost:8000')

const api = axios.create({
  baseURL: BASE,
  timeout: 60000,   // 60s — Render free tier cold start can take ~50s
})


export const getDashboard    = ()           => api.get('/api/dashboard')
export const getForecast     = (hours = 24) => api.get(`/api/forecast?hours=${hours}`)
export const getWeather      = ()           => api.get('/api/weather')
export const getAlerts       = ()           => api.get('/api/alerts')
export const getRecommendation = ()         => api.get('/api/recommendations')
export const getZones        = ()           => api.get('/api/zones')
export const getZoneDetail   = (zoneId)     => api.get(`/api/zones/${zoneId}`)
export const runPredict      = (body)       => api.post('/api/predict', body)

export default api
