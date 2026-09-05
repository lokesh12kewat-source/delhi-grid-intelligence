// src/services/api.js
// Single API client — all components import from here

import axios from 'axios'

// Hardcoded backend URLs — no env var dependency
const RENDER_URL = 'https://delhi-grid-intelligence.onrender.com'
const LOCAL_URL  = 'http://localhost:8000'

const IS_LOCAL = typeof window !== 'undefined' && 
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

const BASE = IS_LOCAL ? LOCAL_URL : RENDER_URL

const api = axios.create({
  baseURL: BASE,
  timeout: 60000,  // 60s — Render free tier cold start can take ~50s
})

export const getDashboard     = ()           => api.get('/api/dashboard')
export const getForecast      = (hours = 24) => api.get(`/api/forecast?hours=${hours}`)
export const getWeather       = ()           => api.get('/api/weather')
export const getAlerts        = ()           => api.get('/api/alerts')
export const getRecommendation = ()          => api.get('/api/recommendations')
export const getZones         = ()           => api.get('/api/zones')
export const getZoneDetail    = (zoneId)     => api.get(`/api/zones/${zoneId}`)
export const runPredict       = (body)       => api.post('/api/predict', body)

export default api


export default api
