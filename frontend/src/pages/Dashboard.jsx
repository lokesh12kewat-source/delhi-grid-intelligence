// src/pages/Dashboard.jsx
import { useEffect, useState, useCallback } from 'react'
import { getDashboard } from '../services/api'
import { KPICard } from '../components/KPICard'
import { ForecastChart } from '../components/ForecastChart'
import { ZoneCard } from '../components/ZoneCard'
import { WeatherPanel } from '../components/WeatherPanel'
import { AlertFeed } from '../components/AlertFeed'
import { RecommendationPanel } from '../components/RecommendationPanel'
import { RiskBadge } from '../components/RiskBadge'
import { RefreshCw, Cpu } from 'lucide-react'

const REFRESH_INTERVAL = 60 * 1000   // 60s auto-refresh

export default function Dashboard() {
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)
  const [lastUpd, setLastUpd] = useState(null)
  const [forecastFull, setForecastFull] = useState([])

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [dashRes] = await Promise.all([getDashboard()])
      setData(dashRes.data)
      setLastUpd(new Date().toLocaleTimeString('en-IN'))
    } catch (e) {
      setError(e.message || 'Failed to load dashboard')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
    const id = setInterval(load, REFRESH_INTERVAL)
    return () => clearInterval(id)
  }, [load])

  const grid    = data?.grid_summary || {}
  const weather = data?.weather || {}
  const zones   = data?.zone_risks || []
  const alerts  = data?.alerts || []
  const rec     = data?.recommendation
  const zoneWx  = data?.zone_weather || []
  const peek    = data?.forecast_preview || []

  // Actuals from the preview (past data would come with forecast)
  const actuals  = []
  const forecast = peek

  if (error) return (
    <div className="max-w-screen-xl mx-auto px-6 py-16 text-center">
      <div className="text-4xl mb-4">⚡</div>
      <div className="text-cyber-red font-bold text-lg mb-2">Backend not connected</div>
      <div className="text-slate-500 text-sm mb-6">{error}</div>
      <div className="text-xs text-slate-600 bg-white/[0.03] rounded-xl p-4 max-w-md mx-auto text-left font-mono">
        <div className="text-cyber-cyan mb-2"># Start the backend first:</div>
        <div>cd backend</div>
        <div>uvicorn app.main:app --reload</div>
      </div>
    </div>
  )

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8">

      {/* Header row */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-extrabold text-white">
            Delhi Grid Intelligence
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            AI-powered demand forecasting · Short-term load prediction · PS-1
          </p>
        </div>
        <div className="flex items-center gap-4">
          {grid.risk_level && <RiskBadge level={grid.risk_level} size="lg" />}
          {lastUpd && (
            <span className="text-xs text-slate-600">Updated {lastUpd}</span>
          )}
          <button
            onClick={load}
            disabled={loading}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white
                       bg-white/[0.04] hover:bg-white/[0.08] px-3 py-2 rounded-lg
                       transition-all border border-white/[0.06]"
          >
            <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <KPICard
          title="Current Demand"
          value={grid.total_demand_mw?.toFixed(0) ?? '—'}
          unit="MW"
          color="cyan"
          icon="⚡"
          subtext="Predicted next hour"
        />
        <KPICard
          title="Grid Capacity"
          value={grid.total_capacity_mw?.toFixed(0) ?? '—'}
          unit="MW"
          color="blue"
          icon="🔋"
          subtext="Configured (demo)"
        />
        <KPICard
          title="Headroom"
          value={grid.headroom_mw?.toFixed(0) ?? '—'}
          unit="MW"
          color={grid.headroom_mw < 500 ? 'red' : grid.headroom_mw < 1500 ? 'yellow' : 'green'}
          icon="📊"
          subtext={`${grid.utilization_pct?.toFixed(1) ?? '—'}% utilized`}
        />
        <KPICard
          title="Active Alerts"
          value={data?.active_alerts ?? '—'}
          color={data?.active_alerts > 0 ? 'orange' : 'green'}
          icon={data?.active_alerts > 0 ? '🚨' : '✅'}
          subtext={`${grid.n_critical_zones ?? 0} critical zone(s)`}
        />
      </div>

      {/* Main content grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Forecast chart — spans 2 cols */}
        <div className="lg:col-span-2">
          <div className="glass-card p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="section-title mb-0">
                <Cpu size={14} className="text-cyber-cyan" />
                Demand Forecast vs Actual
              </div>
              <span className="text-[10px] text-slate-600">
                {data?.model_meta?.model_name && `Model: ${data.model_meta.model_name}`}
              </span>
            </div>
            {loading && !data ? (
              <div className="h-64 flex items-center justify-center text-slate-600 text-sm animate-pulse">
                Loading forecast...
              </div>
            ) : (
              <ForecastChart forecast={forecast} actuals={actuals} />
            )}
          </div>
        </div>

        {/* Right column: weather + alerts */}
        <div className="space-y-6">
          <WeatherPanel weather={weather} zones={zoneWx} />
          <div className="glass-card p-5">
            <div className="section-title">🚨 Alerts</div>
            <AlertFeed alerts={alerts} />
          </div>
        </div>
      </div>

      {/* Zone grid */}
      <div className="mt-6">
        <div className="section-title mb-4">🗺️ Delhi Zones — Current Status</div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {loading && !data
            ? Array(6).fill(0).map((_, i) => (
                <div key={i} className="glass-card p-5 h-36 animate-pulse bg-white/[0.02]" />
              ))
            : zones.map(z => (
                <ZoneCard key={z.zone_id} zone={z} />
              ))
          }
        </div>
      </div>

      {/* AI Recommendation */}
      <div className="mt-6">
        <RecommendationPanel recommendation={rec} />
      </div>

    </div>
  )
}
