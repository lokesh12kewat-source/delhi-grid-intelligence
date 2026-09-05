// src/services/api.js
import axios from 'axios'

const RENDER_URL = 'https://delhi-grid-intelligence.onrender.com'
const LOCAL_URL  = 'http://localhost:8000'

const IS_LOCAL = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

const api = axios.create({
  baseURL: IS_LOCAL ? LOCAL_URL : RENDER_URL,
  timeout: 60000,
})

export const getDashboard      = ()           => api.get('/api/dashboard')
export const getForecast       = (hours = 24) => api.get(`/api/forecast?hours=${hours}`)
export const getWeather        = ()           => api.get('/api/weather')
export const getAlerts         = ()           => api.get('/api/alerts')
export const getRecommendation = ()           => api.get('/api/recommendations')
export const getZones          = ()           => api.get('/api/zones')
export const getZoneDetail     = (zoneId)     => api.get(`/api/zones/${zoneId}`)
export const runPredict        = (body)       => api.post('/api/predict', body)

export default api
