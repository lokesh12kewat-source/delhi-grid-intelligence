// src/pages/ForecastView.jsx  — light theme, animated
import { useEffect, useState } from 'react'
import { getForecast } from '../services/api'
import ForecastChart from '../components/ForecastChart'
import RiskBadge from '../components/RiskBadge'
import { RefreshCw, TrendingUp, Clock, Zap } from 'lucide-react'

const HORIZONS = [6, 12, 24, 48, 72, 168]

export default function ForecastView() {
  const [hours,   setHours]   = useState(24)
  const [data,    setData]    = useState(null)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  const load = async (h) => {
    setLoading(true); setError(null)
    try { const res = await getForecast(h); setData(res.data) }
    catch (e) { setError(e.message) }
    finally { setLoading(false) }
  }

  useEffect(() => { load(hours) }, [hours])

  const fc   = data?.forecast || []
  const ac   = data?.actuals  || []
  const meta = data?.model_meta || {}

  return (
    <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">

      {/* Header */}
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-gray-800 flex items-center gap-2">
            <TrendingUp className="text-teal-500" size={24}/> Demand Forecast
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            AI-powered short-term electricity demand prediction for Delhi grid
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {HORIZONS.map(h => (
            <button key={h} onClick={() => setHours(h)}
              className={`px-3 py-1.5 text-xs font-semibold rounded-lg border transition-all ${
                hours === h
                  ? 'bg-teal-500 border-teal-500 text-white shadow-sm'
                  : 'border-gray-200 text-gray-500 hover:border-teal-300 hover:text-teal-600 bg-white'
              }`}>{h}h
            </button>
          ))}
          <button onClick={() => load(hours)}
            className="ml-1 p-2 rounded-lg border border-gray-200 text-gray-400 hover:text-teal-600 hover:border-teal-300 bg-white transition-all">
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''}/>
          </button>
        </div>
      </div>

      {/* Model badge */}
      {meta.model_name && (
        <div className="flex items-center gap-3 flex-wrap">
          <span className="bg-teal-50 text-teal-700 border border-teal-200 rounded-full px-3 py-0.5 text-xs font-medium">
            🤖 {meta.model_name}
          </span>
          {meta.test_metrics && Object.entries(meta.test_metrics).map(([k,v]) => (
            <span key={k} className="bg-gray-50 text-gray-600 border border-gray-200 rounded-full px-3 py-0.5 text-xs">
              {k}: <b>{v}</b>
            </span>
          ))}
        </div>
      )}

      {error && (
        <div className="section-card border-red-100 bg-red-50 text-red-600 text-sm flex items-center gap-2">
          <Zap size={16}/> {error}
        </div>
      )}

      {/* Chart */}
      {loading
        ? <div className="section-card h-80 flex items-center justify-center">
            <div className="flex flex-col items-center gap-3">
              <div className="w-8 h-8 border-2 border-teal-400 border-t-transparent rounded-full animate-spin"/>
              <p className="text-gray-400 text-sm">Loading forecast...</p>
            </div>
          </div>
        : <ForecastChart forecast={fc} actuals={ac}/>
      }

      {/* Forecast Table */}
      {fc.length > 0 && (
        <div className="section-card">
          <div className="flex items-center gap-2 mb-4">
            <Clock size={16} className="text-teal-500"/>
            <h2 className="text-base font-semibold text-gray-800">Hourly Forecast Detail</h2>
            <span className="text-xs text-gray-400 ml-1">Next {hours} hours</span>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400 text-xs uppercase tracking-wider">
                  <th className="py-2.5 pr-4 text-left font-medium">Time</th>
                  <th className="py-2.5 pr-4 text-left font-medium">Demand</th>
                  <th className="py-2.5 pr-4 text-left font-medium">Utilization</th>
                  <th className="py-2.5 pr-4 text-left font-medium">Headroom</th>
                  <th className="py-2.5 pr-4 text-left font-medium">Temp</th>
                  <th className="py-2.5 text-left font-medium">Risk</th>
                </tr>
              </thead>
              <tbody>
                {fc.slice(0, 48).map((row, i) => {
                  const ts = new Date(row.timestamp)
                  const bgColor = row.risk_level === 'HIGH' ? 'bg-red-50'
                    : row.risk_level === 'MEDIUM' ? 'bg-amber-50'
                    : row.risk_level === 'CRITICAL' ? 'bg-purple-50' : ''
                  return (
                    <tr key={i} className={`border-b border-gray-50 hover:bg-teal-50/30 transition-colors ${bgColor}`}>
                      <td className="py-2 pr-4">
                        <span className="font-mono text-gray-800 font-medium">
                          {ts.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                        <span className="text-gray-400 ml-1.5 text-xs">
                          {ts.toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })}
                        </span>
                      </td>
                      <td className="py-2 pr-4 font-bold text-gray-800">
                        {row.predicted_demand_mw?.toFixed(0)}
                        <span className="text-xs text-gray-400 ml-1 font-normal">MW</span>
                      </td>
                      <td className="py-2 pr-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 bg-gray-100 rounded-full h-1.5">
                            <div className="h-1.5 rounded-full transition-all"
                              style={{
                                width: `${Math.min(row.utilization_pct||0, 100)}%`,
                                background: row.utilization_pct > 90 ? '#ef4444'
                                  : row.utilization_pct > 75 ? '#f59e0b' : '#14b8a6'
                              }}/>
                          </div>
                          <span className="text-xs text-gray-600">{row.utilization_pct?.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="py-2 pr-4 text-gray-600 text-xs">{row.headroom_mw?.toFixed(0)} MW</td>
                      <td className="py-2 pr-4 text-gray-600 text-xs">
                        {row.temperature_c != null ? `${row.temperature_c.toFixed(1)}°C` : '—'}
                      </td>
                      <td className="py-2"><RiskBadge level={row.risk_level}/></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
