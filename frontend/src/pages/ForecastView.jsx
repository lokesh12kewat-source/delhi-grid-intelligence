// src/pages/ForecastView.jsx
import { useEffect, useState } from 'react'
import { getForecast } from '../services/api'
import ForecastChart from '../components/ForecastChart'
import RiskBadge from '../components/RiskBadge'
import { RefreshCw } from 'lucide-react'

const HORIZONS = [6, 12, 24, 48, 72, 168]

export default function ForecastView() {
  const [hours, setHours] = useState(24)
  const [data,  setData]  = useState(null)
  const [loading, setLoad] = useState(true)
  const [error, setErr]   = useState(null)

  const load = async (h) => {
    setLoad(true); setErr(null)
    try {
      const res = await getForecast(h)
      setData(res.data)
    } catch (e) { setErr(e.message) }
    finally { setLoad(false) }
  }

  useEffect(() => { load(hours) }, [hours])

  const fc = data?.forecast || []
  const ac = data?.actuals  || []

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Demand Forecast</h1>
          <p className="text-sm text-slate-500 mt-1">AI-generated short-term electricity demand prediction</p>
        </div>
        <div className="flex items-center gap-2">
          {HORIZONS.map(h => (
            <button
              key={h}
              onClick={() => setHours(h)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                hours === h
                  ? 'bg-cyber-cyan/10 border-cyber-cyan/40 text-cyber-cyan'
                  : 'border-white/[0.06] text-slate-400 hover:text-white hover:border-white/20'
              }`}
            >{h}h</button>
          ))}
          <button onClick={() => load(hours)} className="ml-2 text-slate-400 hover:text-white p-1.5">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>
      </div>

      {error && <div className="text-cyber-red text-sm mb-4">{error}</div>}

      {/* Chart */}
      <div className="glass-card p-5 mb-6">
        <div className="text-sm font-semibold text-slate-400 mb-4">
          Next {hours} hours · Predicted vs Historical Actuals
          {data?.model_meta?.model_name && (
            <span className="ml-3 text-xs text-slate-600">
              {data.model_meta.model_name}
            </span>
          )}
        </div>
        {loading
          ? <div className="h-80 flex items-center justify-center text-slate-600 animate-pulse">Loading...</div>
          : <ForecastChart forecast={fc} actuals={ac} />
        }
      </div>

      {/* Model metrics */}
      {data?.model_meta?.test_metrics && (
        <div className="glass-card p-5 mb-6">
          <div className="section-title">📊 Model Test Performance</div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(data.model_meta.test_metrics).map(([k, v]) => (
              <div key={k} className="text-center">
                <div className="text-2xl font-extrabold text-cyber-cyan">{v}</div>
                <div className="text-xs text-slate-500 uppercase tracking-widest">{k}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Forecast table */}
      <div className="glass-card p-5">
        <div className="section-title">📋 Hourly Forecast Detail</div>
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-white/[0.06] text-slate-500 uppercase tracking-widest text-[10px]">
                <th className="py-2 pr-4">Time</th>
                <th className="py-2 pr-4">Demand (MW)</th>
                <th className="py-2 pr-4">Utilization</th>
                <th className="py-2 pr-4">Headroom (MW)</th>
                <th className="py-2 pr-4">Temp (°C)</th>
                <th className="py-2">Risk</th>
              </tr>
            </thead>
            <tbody>
              {fc.slice(0, 48).map((row, i) => {
                const ts = new Date(row.timestamp)
                return (
                  <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                    <td className="py-1.5 pr-4 font-mono text-slate-400">
                      {ts.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                      <span className="text-slate-600 ml-1 text-[9px]">
                        {ts.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                      </span>
                    </td>
                    <td className="py-1.5 pr-4 font-bold text-white">
                      {row.predicted_demand_mw?.toFixed(0)}
                    </td>
                    <td className="py-1.5 pr-4 text-slate-400">
                      {row.utilization_pct?.toFixed(1)}%
                    </td>
                    <td className="py-1.5 pr-4 text-slate-400">
                      {row.headroom_mw?.toFixed(0)}
                    </td>
                    <td className="py-1.5 pr-4 text-slate-400">
                      {row.temperature_c?.toFixed(1) ?? '—'}
                    </td>
                    <td className="py-1.5">
                      <RiskBadge level={row.risk_level} />
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
