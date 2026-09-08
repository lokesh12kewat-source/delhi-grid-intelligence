// src/services/api.js
import axios from 'axios'

const RENDER_URL = 'https://delhi-grid-intelligence.onrender.com'
const LOCAL_URL  = 'http://localhost:8000'

const IS_LOCAL = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

const api = axios.create({
  baseURL: IS_LOCAL ? LOCAL_URL : RENDER_URL,
  timeout: 90000,   // 90s — covers full Render cold-start (~50s) + processing
})

// ── Auto-retry with exponential backoff ─────────────────────────────────────
// On Render free tier the first request after inactivity can fail or be slow.
// We silently retry up to 4 times (total wait ~60s) before showing an error.
export async function withRetry(fn, maxAttempts = 4) {
  let delay = 8000   // start: 8s between retries
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      return await fn()
    } catch (err) {
      if (attempt === maxAttempts) throw err
      await new Promise(r => setTimeout(r, delay))
      delay = Math.min(delay * 1.4, 20000)   // cap at 20s
    }
  }
}

export const getDashboard      = ()           => withRetry(() => api.get('/api/dashboard'))
export const getForecast       = (hours = 24) => withRetry(() => api.get(`/api/forecast?hours=${hours}`))
export const getWeather        = ()           => withRetry(() => api.get('/api/weather'))
export const getAlerts         = ()           => withRetry(() => api.get('/api/alerts'))
export const getRecommendation = ()           => withRetry(() => api.get('/api/recommendations'))
export const getZones          = ()           => withRetry(() => api.get('/api/zones'))
export const getZoneDetail     = (zoneId)     => withRetry(() => api.get(`/api/zones/${zoneId}`))
export const runPredict        = (body)       => withRetry(() => api.post('/api/predict', body))

export default api
