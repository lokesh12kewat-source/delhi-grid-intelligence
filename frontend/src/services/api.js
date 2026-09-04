// src/services/api.js
// Single API client — all components import from here

import axios from 'axios'

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: BASE,
  timeout: 30000,
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
