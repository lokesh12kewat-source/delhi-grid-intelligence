export default function KPICard({ title, value, unit, subtitle, icon: Icon, color = 'teal' }) {
  const colors = {
    teal:   { bg: 'bg-teal-50',   text: 'text-teal-600',   icon: 'text-teal-500'   },
    red:    { bg: 'bg-red-50',    text: 'text-red-600',    icon: 'text-red-500'    },
    amber:  { bg: 'bg-amber-50',  text: 'text-amber-600',  icon: 'text-amber-500'  },
    blue:   { bg: 'bg-blue-50',   text: 'text-blue-600',   icon: 'text-blue-500'   },
    green:  { bg: 'bg-green-50',  text: 'text-green-600',  icon: 'text-green-500'  },
    purple: { bg: 'bg-purple-50', text: 'text-purple-600', icon: 'text-purple-500' },
  }
  const c = colors[color] || colors.teal

  return (
    <div className="section-card flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-500">{title}</span>
        {Icon && (
          <span className={`w-8 h-8 rounded-lg ${c.bg} flex items-center justify-center`}>
            <Icon size={16} className={c.icon} />
          </span>
        )}
      </div>
      <div className="flex items-end gap-1">
        <span className="text-2xl font-bold text-gray-800">{value ?? '—'}</span>
        {unit && <span className="text-sm text-gray-400 mb-0.5">{unit}</span>}
      </div>
      {subtitle && <p className={`text-xs font-medium ${c.text}`}>{subtitle}</p>}
    </div>
  )
}
