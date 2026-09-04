// src/pages/Alerts.jsx
import { useEffect, useState } from 'react'
import { getAlerts, getRecommendation } from '../services/api'
import { AlertFeed } from '../components/AlertFeed'
import { RecommendationPanel } from '../components/RecommendationPanel'
import { RefreshCw } from 'lucide-react'

export default function Alerts() {
  const [alertData, setAlerts] = useState(null)
  const [rec,       setRec]    = useState(null)
  const [loading,   setLoad]   = useState(true)
  const [recLoad,   setRecLoad]= useState(true)

  const loadAlerts = async () => {
    setLoad(true)
    try {
      const res = await getAlerts()
      setAlerts(res.data)
    } catch (e) { console.error(e) }
    finally { setLoad(false) }
  }

  const loadRec = async () => {
    setRecLoad(true)
    try {
      const res = await getRecommendation()
      setRec(res.data)
    } catch (e) { console.error(e) }
    finally { setRecLoad(false) }
  }

  useEffect(() => {
    loadAlerts()
    loadRec()
  }, [])

  const alerts = alertData?.alerts || []

  return (
    <div className="max-w-screen-xl mx-auto px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-extrabold text-white">Alerts & Recommendations</h1>
          <p className="text-sm text-slate-500 mt-1">
            Capacity risk alerts + AI-powered operator recommendations
          </p>
        </div>
        <button
          onClick={() => { loadAlerts(); loadRec() }}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white
                     bg-white/[0.04] px-3 py-2 rounded-lg border border-white/[0.06]"
        >
          <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts column */}
        <div>
          <div className="section-title">🚨 Active Capacity Alerts</div>
          <div className="text-xs text-slate-600 mb-4">
            {alertData?.total != null
              ? `${alertData.total} alert(s) — thresholds configurable`
              : 'Loading alerts...'
            }
          </div>
          {loading
            ? <div className="glass-card p-8 text-center text-slate-600 text-sm animate-pulse">
                Loading alerts...
              </div>
            : <AlertFeed alerts={alerts} />
          }
        </div>

        {/* Recommendation column */}
        <div>
          <div className="section-title">✨ AI Recommendation</div>
          <div className="text-xs text-slate-600 mb-4">
            Gemini LLM explains structured risk assessment
          </div>
          {recLoad
            ? <div className="glass-card p-8 text-center text-slate-600 text-sm animate-pulse">
                Generating recommendation...
              </div>
            : <RecommendationPanel recommendation={rec} />
          }
        </div>
      </div>

      {/* Legend */}
      <div className="mt-8 glass-card p-5">
        <div className="section-title">📌 Risk Level Legend</div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
          {[
            { level: 'LOW',      desc: '< 60% capacity',  color: 'text-cyber-green'  },
            { level: 'MEDIUM',   desc: '60–75% capacity', color: 'text-cyber-yellow' },
            { level: 'HIGH',     desc: '75–90% capacity', color: 'text-[#ff6600]'    },
            { level: 'CRITICAL', desc: '> 90% capacity',  color: 'text-cyber-red'    },
          ].map(r => (
            <div key={r.level} className="flex items-start gap-2">
              <div className={`font-bold ${r.color} mt-0.5`}>●</div>
              <div>
                <div className={`font-bold ${r.color}`}>{r.level}</div>
                <div className="text-slate-500">{r.desc}</div>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-3 text-[10px] text-slate-600 italic">
          Thresholds are configurable via .env and are not official SLDC/POSOCO limits.
        </div>
      </div>
    </div>
  )
}
