// src/components/RiskBadge.jsx
const CONFIG = {
  LOW:      { bg: 'bg-cyber-green/10', text: 'text-cyber-green', border: 'border-cyber-green/30' },
  MEDIUM:   { bg: 'bg-cyber-yellow/10', text: 'text-cyber-yellow', border: 'border-cyber-yellow/30' },
  HIGH:     { bg: 'bg-[#ff6600]/10', text: 'text-[#ff6600]', border: 'border-[#ff6600]/30' },
  CRITICAL: { bg: 'bg-cyber-red/10', text: 'text-cyber-red', border: 'border-cyber-red/30' },
  UNKNOWN:  { bg: 'bg-slate-500/10', text: 'text-slate-400', border: 'border-slate-500/30' },
}

export function RiskBadge({ level, size = 'sm' }) {
  const c = CONFIG[level] || CONFIG.UNKNOWN
  const sz = size === 'lg' ? 'px-3 py-1 text-sm' : 'px-2.5 py-0.5 text-xs'
  return (
    <span className={`risk-badge border ${c.bg} ${c.text} ${c.border} ${sz}`}>
      {level === 'CRITICAL' && <span className="mr-1">⚡</span>}
      {level}
    </span>
  )
}
