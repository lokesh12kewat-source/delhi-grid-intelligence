// src/components/ZoneCard.jsx
import { RiskBadge } from './RiskBadge'

const BORDER_COLOR = {
  LOW:      'border-t-cyber-green',
  MEDIUM:   'border-t-cyber-yellow',
  HIGH:     'border-t-[#ff6600]',
  CRITICAL: 'border-t-cyber-red',
  UNKNOWN:  'border-t-slate-500',
}

const PULSE = {
  CRITICAL: 'animate-pulse-red',
}

export function ZoneCard({ zone, onClick }) {
  const risk = zone.risk_level || 'UNKNOWN'
  const border = BORDER_COLOR[risk] || BORDER_COLOR.UNKNOWN
  const pulse  = PULSE[risk]  || ''
  const util   = zone.utilization_pct ?? 0

  return (
    <div
      className={`zone-card ${border} ${pulse}`}
      onClick={() => onClick?.(zone)}
    >
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-xs text-slate-500 uppercase tracking-widest font-semibold">
            {zone.discom || zone.zone_id}
          </div>
          <div className="text-sm font-bold text-white mt-0.5">
            {zone.zone_name || zone.zone_id}
          </div>
        </div>
        <RiskBadge level={risk} />
      </div>

      <div className="text-3xl font-extrabold text-white mb-1">
        {zone.predicted_demand_mw != null ? `${zone.predicted_demand_mw.toFixed(0)}` : '—'}
        <span className="text-base font-medium text-slate-400 ml-1">MW</span>
      </div>

      {/* Utilization bar */}
      <div className="mt-3">
        <div className="flex justify-between text-[10px] text-slate-500 mb-1">
          <span>Utilization</span>
          <span>{util.toFixed(1)}%</span>
        </div>
        <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700"
            style={{
              width: `${Math.min(util, 100)}%`,
              background: risk === 'CRITICAL' ? '#ff3366'
                        : risk === 'HIGH'     ? '#ff6600'
                        : risk === 'MEDIUM'   ? '#ffcc00'
                        : '#00ff88',
            }}
          />
        </div>
      </div>

      <div className="mt-2 text-[10px] text-slate-500">
        Headroom: <span className="text-slate-400 font-semibold">
          {zone.headroom_mw != null ? `${zone.headroom_mw.toFixed(0)} MW` : '—'}
        </span>
      </div>
    </div>
  )
}
