// src/components/AlertFeed.jsx
import { RiskBadge } from './RiskBadge'
import { AlertTriangle, Zap } from 'lucide-react'

export function AlertFeed({ alerts = [] }) {
  if (alerts.length === 0) {
    return (
      <div className="glass-card p-5 flex flex-col items-center justify-center gap-3 min-h-[160px]">
        <div className="text-3xl">✅</div>
        <div className="text-sm text-cyber-green font-semibold">All Zones Normal</div>
        <div className="text-xs text-slate-500">No active capacity alerts</div>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {alerts.map((alert, i) => (
        <div
          key={i}
          className="glass-card p-4 border-l-4"
          style={{ borderLeftColor: alert.risk_color || '#ff3366' }}
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <div className="flex items-center gap-2">
              {alert.risk_level === 'CRITICAL'
                ? <Zap size={14} className="text-cyber-red flex-shrink-0" />
                : <AlertTriangle size={14} className="text-[#ff6600] flex-shrink-0" />
              }
              <span className="text-sm font-bold text-white">
                {alert.zone_id?.replace('delhi_','').toUpperCase()} DELHI
              </span>
            </div>
            <RiskBadge level={alert.risk_level} />
          </div>

          <div className="text-xs text-slate-400 mb-2">{alert.message}</div>

          <div className="flex gap-4 text-[10px] text-slate-500">
            <span>Load: <strong className="text-slate-300">{alert.predicted_demand_mw?.toFixed(0)} MW</strong></span>
            <span>Capacity: <strong className="text-slate-300">{alert.capacity_mw?.toFixed(0)} MW</strong></span>
            <span>Headroom: <strong className="text-cyber-yellow">{alert.headroom_mw?.toFixed(0)} MW</strong></span>
          </div>
        </div>
      ))}
    </div>
  )
}
