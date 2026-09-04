// src/components/KPICard.jsx
export function KPICard({ title, value, unit, subtext, trend, color = 'cyan', icon }) {
  const colorMap = {
    cyan:   'border-cyber-cyan/30 text-cyber-cyan',
    green:  'border-cyber-green/30 text-cyber-green',
    red:    'border-cyber-red/30 text-cyber-red',
    yellow: 'border-cyber-yellow/30 text-cyber-yellow',
    orange: 'border-[#ff6600]/30 text-[#ff6600]',
    blue:   'border-cyber-blue/30 text-cyber-blue',
  }
  const cls = colorMap[color] || colorMap.cyan

  return (
    <div className={`kpi-card border-b-2 ${cls}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-widest">{title}</span>
        {icon && <span className="text-lg">{icon}</span>}
      </div>
      <div className={`text-3xl font-extrabold ${cls.split(' ')[1]}`}>
        {value ?? '—'}
        {unit && <span className="text-base font-medium text-slate-400 ml-1">{unit}</span>}
      </div>
      {subtext && <div className="text-xs text-slate-500">{subtext}</div>}
      {trend && (
        <div className={`text-xs font-semibold ${trend.startsWith('↑') ? 'text-cyber-red' : 'text-cyber-green'}`}>
          {trend}
        </div>
      )}
    </div>
  )
}
