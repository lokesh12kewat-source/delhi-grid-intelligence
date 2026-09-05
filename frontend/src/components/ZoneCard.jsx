import RiskBadge from './RiskBadge'

export default function ZoneCard({ zone }) {
  const util = zone.utilization_pct ?? 0
  const barColor = util >= 90 ? 'bg-red-400' : util >= 75 ? 'bg-amber-400' : util >= 60 ? 'bg-yellow-400' : 'bg-teal-400'
  const name = (zone.zone_id || zone.name || '').replace('delhi_', '').replace('_', ' ')

  return (
    <div className="zone-card">
      <div className="flex items-start justify-between mb-2">
        <p className="text-xs font-semibold text-gray-700 capitalize">{name}</p>
        <RiskBadge level={zone.risk_level} />
      </div>
      <p className="text-xl font-bold text-gray-800 mb-1">
        {zone.demand_mw?.toFixed(0) ?? '—'}
        <span className="text-xs font-normal text-gray-400 ml-1">MW</span>
      </p>
      <div className="w-full bg-gray-100 rounded-full h-1.5 mb-1">
        <div
          className={`h-1.5 rounded-full transition-all ${barColor}`}
          style={{ width: `${Math.min(util, 100)}%` }}
        />
      </div>
      <p className="text-xs text-gray-400">{util.toFixed(1)}% utilized</p>
    </div>
  )
}
