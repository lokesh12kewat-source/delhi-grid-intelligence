// src/pages/ZoneAnalysis.jsx
import { useEffect, useState } from 'react'
import { getZones, getZoneDetail } from '../services/api'
import ZoneCard from '../components/ZoneCard'
import ForecastChart from '../components/ForecastChart'
import RiskBadge from '../components/RiskBadge'

export default function ZoneAnalysis() {
  const [zones,   setZones]  = useState([])
  const [detail,  setDetail] = useState(null)
  const [loading, setLoad]   = useState(true)
  const [error,   setErr]    = useState(null)

  useEffect(() => {
    const load = async () => {
      setLoad(true)
      try {
        const res = await getZones()
        setZones(res.data.zones || [])
      } catch (e) { setErr(e.message) }
      finally { setLoad(false) }
    }
    load()
  }, [])

  const handleZoneClick = async (zone) => {
    try {
      const res = await getZoneDetail(zone.zone_id)
      setDetail(res.data)
    } catch (e) { console.error(e) }
  }

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-extrabold text-white mb-2">Zone Analysis</h1>
      <p className="text-sm text-slate-500 mb-8">
        Delhi electricity demand by DISCOM zone · Click a zone for detailed 24h forecast
      </p>

      {error && <div className="text-cyber-red text-sm mb-4">{error}</div>}

      {/* Zone grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {loading
          ? Array(6).fill(0).map((_, i) => (
              <div key={i} className="glass-card p-5 h-40 animate-pulse bg-white/[0.02]" />
            ))
          : zones.map(z => (
              <ZoneCard key={z.zone_id} zone={z} onClick={handleZoneClick} />
            ))
        }
      </div>

      {/* Zone detail panel */}
      {detail && (
        <div className="glass-card p-6">
          <div className="flex items-center justify-between mb-6">
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-widest">{detail.discom}</div>
              <h2 className="text-xl font-bold text-white">{detail.zone_name}</h2>
              <div className="text-xs text-slate-500 mt-0.5">{detail.description}</div>
            </div>
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-xs text-slate-500">Capacity</div>
                <div className="text-lg font-bold text-white">{detail.capacity_mw?.toFixed(0)} MW</div>
                <div className="text-[9px] text-slate-600">{detail.capacity_note}</div>
              </div>
            </div>
          </div>

          {detail.forecast_24h?.length > 0 && (
            <>
              <div className="text-sm font-semibold text-slate-400 mb-4">24h Zone Demand Forecast</div>
              <ForecastChart
                forecast={detail.forecast_24h.map(f => ({
                  ...f,
                  predicted_demand_mw: f.predicted_demand_mw,
                }))}
                actuals={detail.actuals_24h || []}
              />
            </>
          )}

          {/* Zone forecast table */}
          <div className="mt-6 overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead>
                <tr className="border-b border-white/[0.06] text-slate-500 uppercase tracking-widest text-[10px]">
                  <th className="py-2 pr-4">Hour</th>
                  <th className="py-2 pr-4">Demand (MW)</th>
                  <th className="py-2 pr-4">Utilization</th>
                  <th className="py-2 pr-4">Headroom</th>
                  <th className="py-2">Risk</th>
                </tr>
              </thead>
              <tbody>
                {(detail.forecast_24h || []).slice(0, 24).map((row, i) => {
                  const ts = new Date(row.timestamp)
                  return (
                    <tr key={i} className="border-b border-white/[0.03] hover:bg-white/[0.02]">
                      <td className="py-1.5 pr-4 font-mono text-slate-400">
                        {ts.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      <td className="py-1.5 pr-4 font-bold text-white">
                        {row.predicted_demand_mw?.toFixed(0)}
                      </td>
                      <td className="py-1.5 pr-4 text-slate-400">{row.utilization_pct?.toFixed(1)}%</td>
                      <td className="py-1.5 pr-4 text-slate-400">{row.headroom_mw?.toFixed(0)} MW</td>
                      <td className="py-1.5"><RiskBadge level={row.risk_level} /></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!detail && !loading && (
        <div className="glass-card p-10 text-center">
          <div className="text-3xl mb-3">👆</div>
          <div className="text-sm text-slate-500">Click any zone card above to see its 24h forecast</div>
        </div>
      )}
    </div>
  )
}
