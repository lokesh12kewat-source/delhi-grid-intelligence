// src/pages/ZoneAnalysis.jsx
import { useEffect, useState } from 'react'
import { getZones, getZoneDetail } from '../services/api'
import ZoneCard from '../components/ZoneCard'
import ForecastChart from '../components/ForecastChart'
import RiskBadge from '../components/RiskBadge'

export default function ZoneAnalysis() {
  const [zones,   setZones]  = useState([])
  const [detail,  setDetail] = useState(null)
  const [selected,setSelected] = useState(null)
  const [loading, setLoad]   = useState(true)
  const [detailLoad, setDetailLoad] = useState(false)
  const [error,   setErr]    = useState(null)

  useEffect(() => {
    getZones()
      .then(r => { setZones(r.data.zones || []); setLoad(false) })
      .catch(e => { setErr(e.message); setLoad(false) })
  }, [])

  const handleZoneClick = async (zone) => {
    setSelected(zone.zone_id)
    setDetailLoad(true)
    try {
      const res = await getZoneDetail(zone.zone_id)
      setDetail(res.data)
    } catch (e) { console.error(e) }
    finally { setDetailLoad(false) }
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Zone Analysis</h1>
      <p className="text-sm text-gray-400 mb-6">
        Delhi electricity demand by DISCOM zone · Click a zone for its 24h forecast
      </p>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-600 text-sm mb-4">
          {error}
        </div>
      )}

      {/* Zone grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        {loading
          ? Array(6).fill(0).map((_, i) => (
              <div key={i} className="zone-card h-36 animate-pulse bg-gray-100" />
            ))
          : zones.map(z => (
              <div
                key={z.zone_id}
                onClick={() => handleZoneClick(z)}
                className={`cursor-pointer transition-all ${selected === z.zone_id ? 'ring-2 ring-teal-400 ring-offset-2' : ''}`}
              >
                <ZoneCard zone={z} />
              </div>
            ))
        }
      </div>

      {/* Zone detail panel */}
      {detailLoad && (
        <div className="section-card text-center py-10 text-gray-400">
          Loading zone detail...
        </div>
      )}

      {detail && !detailLoad && (
        <div className="section-card">
          {/* Header */}
          <div className="flex items-start justify-between mb-6 flex-wrap gap-3">
            <div>
              <p className="text-xs text-teal-600 font-semibold uppercase tracking-widest">{detail.discom}</p>
              <h2 className="text-xl font-bold text-gray-800">{detail.zone_name}</h2>
              <p className="text-xs text-gray-400 mt-0.5">{detail.description}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-gray-400">Zone Capacity</p>
              <p className="text-2xl font-bold text-gray-800">{detail.capacity_mw?.toFixed(0)} <span className="text-sm font-normal text-gray-400">MW</span></p>
            </div>
          </div>

          {/* Chart */}
          {detail.forecast_24h?.length > 0 && (
            <div className="mb-6">
              <p className="text-sm font-semibold text-gray-600 mb-3">24h Zone Demand Forecast</p>
              <ForecastChart
                forecastData={detail.forecast_24h}
                actualsData={detail.actuals_24h || []}
              />
            </div>
          )}

          {/* Table */}
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 text-xs text-gray-400 uppercase tracking-wider">
                  <th className="py-2 pr-4 text-left">Hour</th>
                  <th className="py-2 pr-4 text-left">Demand</th>
                  <th className="py-2 pr-4 text-left">Utilization</th>
                  <th className="py-2 pr-4 text-left">Headroom</th>
                  <th className="py-2 text-left">Risk</th>
                </tr>
              </thead>
              <tbody>
                {(detail.forecast_24h || []).slice(0, 24).map((row, i) => {
                  const ts = new Date(row.timestamp)
                  return (
                    <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 pr-4 font-mono text-gray-500 text-xs">
                        {ts.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true })}
                      </td>
                      <td className="py-2 pr-4 font-bold text-gray-800">
                        {row.predicted_demand_mw?.toFixed(0)} <span className="text-xs font-normal text-gray-400">MW</span>
                      </td>
                      <td className="py-2 pr-4 text-gray-500">{row.utilization_pct?.toFixed(1)}%</td>
                      <td className="py-2 pr-4 text-gray-500">{row.headroom_mw?.toFixed(0)} MW</td>
                      <td className="py-2"><RiskBadge level={row.risk_level} /></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!detail && !loading && !detailLoad && (
        <div className="section-card py-12 text-center">
          <div className="text-4xl mb-3">👆</div>
          <p className="text-gray-400 text-sm">Click any zone card above to see its 24h forecast</p>
        </div>
      )}
    </div>
  )
}
