import { useEffect, useState } from 'react'
import { getDashboard } from '../services/api'
import KPICard from '../components/KPICard'
import ForecastChart from '../components/ForecastChart'
import ZoneCard from '../components/ZoneCard'
import AlertFeed from '../components/AlertFeed'
import RecommendationPanel from '../components/RecommendationPanel'
import WeatherPanel from '../components/WeatherPanel'
import { Activity, Zap, Thermometer, AlertTriangle, TrendingUp, Wind } from 'lucide-react'

export default function Dashboard() {
  const [data, setData]   = useState(null)
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getDashboard()
      .then(r => { setData(r.data); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [])

  const grid    = data?.grid_summary   || {}
  const zones   = data?.zone_risks     || {}
  const weather = data?.weather        || {}
  const peak    = data?.peak_info      || {}
  const model   = data?.model_meta     || {}

  return (
    <div>
      {/* ── Hero Section ── */}
      <div className="hero-section">
        <div className="hero-bg" />
        <div className="hero-overlay" />
        <div className="hero-content w-full">
          <p className="text-white/80 text-xs tracking-[0.25em] uppercase font-medium mb-3">
            Delhi Electricity Intelligence
          </p>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-3 drop-shadow-lg">
            How Delhi{' '}
            <span className="text-teal-300">Uses Power</span>
          </h1>
          <p className="text-white/75 text-base max-w-md mx-auto mb-10">
            Explore how weather, temperature and time influence electricity demand across Delhi.
          </p>

          {/* ── KPI Cards floating over hero ── */}
          {loading ? (
            <div className="flex gap-4 justify-center flex-wrap px-4">
              {[1,2,3,4].map(i => (
                <div key={i} className="kpi-card w-44 h-24 animate-pulse bg-white/60" />
              ))}
            </div>
          ) : error ? (
            <div className="glass-card px-6 py-4 text-center max-w-sm mx-auto">
              <Zap className="mx-auto mb-2 text-red-400" size={24} />
              <p className="text-red-600 font-semibold text-sm">Backend not connected</p>
              <p className="text-gray-500 text-xs mt-1">{error}</p>
              <code className="mt-3 block text-xs bg-gray-100 rounded p-2 text-gray-600">
                # Start the backend first:{'\n'}
                cd backend{'\n'}
                uvicorn app.main:app --reload
              </code>
            </div>
          ) : (
            <div className="flex gap-4 justify-center flex-wrap px-4">
              <div className="kpi-card min-w-[160px]">
                <p className="text-xs text-gray-500 mb-1">Current Demand</p>
                <p className="text-2xl font-bold text-gray-800">
                  {grid.current_demand_mw?.toLocaleString() ?? '—'}
                  <span className="text-sm font-normal text-gray-500 ml-1">MW</span>
                </p>
                <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
                  <TrendingUp size={11} /> Live forecast
                </p>
              </div>

              <div className="kpi-card min-w-[160px]">
                <p className="text-xs text-gray-500 mb-1">Today's Peak</p>
                <p className="text-2xl font-bold text-gray-800">
                  {peak.peak_demand_mw?.toLocaleString() ?? grid.current_demand_mw?.toLocaleString() ?? '—'}
                  <span className="text-sm font-normal text-gray-500 ml-1">MW</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  {peak.peak_hour ? `expected ${peak.peak_hour}` : 'rolling 24h'}
                </p>
              </div>

              <div className="kpi-card min-w-[160px]">
                <p className="text-xs text-gray-500 mb-1">Temperature</p>
                <p className="text-2xl font-bold text-gray-800">
                  {weather.temperature_c != null ? Math.round(weather.temperature_c) : '—'}
                  <span className="text-sm font-normal text-gray-500 ml-1">°C</span>
                </p>
                <p className="text-xs text-blue-500 mt-1 flex items-center gap-1">
                  <Wind size={11} /> {weather.humidity_pct ?? '—'}% humidity
                </p>
              </div>

              <div className="kpi-card min-w-[160px]">
                <p className="text-xs text-gray-500 mb-1">Grid Utilization</p>
                <p className="text-2xl font-bold text-gray-800">
                  {grid.utilization_pct?.toFixed(1) ?? '—'}
                  <span className="text-sm font-normal text-gray-500 ml-1">%</span>
                </p>
                <p className={`text-xs mt-1 font-medium ${
                  grid.risk_level === 'LOW' ? 'text-green-600' :
                  grid.risk_level === 'MEDIUM' ? 'text-yellow-600' :
                  grid.risk_level === 'HIGH' ? 'text-red-600' : 'text-purple-600'
                }`}>
                  ● {grid.risk_level ?? 'LOW'} risk
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Main Content ── */}
      <div className="max-w-7xl mx-auto px-6 py-10 space-y-8">

        {/* ── Model accuracy badge ── */}
        {model.test_metrics && (
          <div className="flex items-center gap-3 flex-wrap">
            <span className="text-xs uppercase tracking-widest text-gray-400 font-semibold">The Energy Story</span>
            <span className="bg-teal-50 text-teal-700 border border-teal-200 rounded-full px-3 py-0.5 text-xs font-medium">
              Model: {model.model_name} · MAPE {model.test_metrics?.MAPE}% · R² {model.test_metrics?.R2}
            </span>
          </div>
        )}

        {/* ── Forecast Chart ── */}
        {data && (
          <div className="section-card">
            <h2 className="text-lg font-semibold text-gray-800 mb-1">24-Hour Demand Forecast</h2>
            <p className="text-xs text-gray-400 mb-4">Predicted vs actual demand with risk bands</p>
            <ForecastChart forecastData={data.forecast_preview?.forecast || []} actualsData={data.forecast_preview?.actuals || []} />
          </div>
        )}

        {/* ── Zone Cards ── */}
        {data && Object.keys(zones).length > 0 && (
          <div>
            <h2 className="text-lg font-semibold text-gray-800 mb-4">Delhi Through Different Zones</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
              {Object.entries(zones).map(([id, z]) => (
                <ZoneCard key={id} zone={{ zone_id: id, ...z }} />
              ))}
            </div>
          </div>
        )}

        {/* ── Weather + AI Recommendation ── */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="section-card">
              <h2 className="text-base font-semibold text-gray-800 mb-4">Live Weather</h2>
              <WeatherPanel weather={data.weather} zoneWeather={data.zone_weather} />
            </div>
            <div className="section-card">
              <h2 className="text-base font-semibold text-gray-800 mb-4">AI Recommendation</h2>
              <RecommendationPanel data={data.recommendation} />
            </div>
          </div>
        )}

        {/* ── Alerts ── */}
        {data && (
          <div className="section-card">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Active Alerts</h2>
            <AlertFeed alerts={data.alerts || []} />
          </div>
        )}
      </div>
    </div>
  )
}
