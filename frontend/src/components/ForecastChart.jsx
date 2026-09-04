// src/components/ForecastChart.jsx
import {
  ResponsiveContainer, ComposedChart, Area, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ReferenceLine
} from 'recharts'

// Format ISO timestamp to HH:MM using native JS (no date-fns needed)
const fmtTime = (isoStr) => {
  try {
    const d = new Date(isoStr)
    return d.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })
  } catch { return isoStr?.substring(11, 16) || '' }
}


const COLORS = {
  predicted: '#00ffff',
  actual:    '#8a2be2',
  fill:      'rgba(0,255,255,0.08)',
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="glass-card p-3 text-xs space-y-1 min-w-[160px]">
      <div className="text-slate-400 font-medium mb-1">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="flex justify-between gap-4" style={{ color: p.color }}>
          <span>{p.name}</span>
          <span className="font-bold">{p.value != null ? `${p.value.toFixed(0)} MW` : '—'}</span>
        </div>
      ))}
    </div>
  )
}

export function ForecastChart({ forecast = [], actuals = [], showConfidence = false }) {
  // Merge actuals + forecast into one timeline
  const actualMap = {}
  actuals.forEach(a => {
    const key = a.timestamp?.substring(0, 16)
    if (key) actualMap[key] = a.actual_demand_mw
  })

  const data = [
    ...actuals.map(a => ({
      time: fmtTime(a.timestamp),
      actual: Math.round(a.actual_demand_mw),
      predicted: null,
      type: 'actual',
    })),
    ...forecast.map(f => ({
      time: fmtTime(f.timestamp),
      actual: null,
      predicted: Math.round(f.predicted_demand_mw),
      risk: f.risk_level,
      type: 'forecast',
    })),
  ]

  // Find separation index for reference line
  const splitIdx = actuals.length

  return (
    <ResponsiveContainer width="100%" height={360}>
      <ComposedChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#00ffff" stopOpacity={0.15}/>
            <stop offset="95%" stopColor="#00ffff" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
        <XAxis
          dataKey="time"
          tick={{ fontSize: 11, fill: '#64748b' }}
          tickLine={false}
          interval={Math.floor(data.length / 8)}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#64748b' }}
          tickLine={false}
          axisLine={false}
          tickFormatter={v => `${v}MW`}
          width={58}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend
          iconType="circle" iconSize={8}
          formatter={v => <span className="text-xs text-slate-400">{v}</span>}
        />

        {/* Actual demand line */}
        <Line
          type="monotone" dataKey="actual" name="Actual Demand"
          stroke={COLORS.actual} strokeWidth={2}
          strokeDasharray="5 3"
          dot={false} connectNulls={false}
        />

        {/* Predicted demand with gradient fill */}
        <Area
          type="monotone" dataKey="predicted" name="AI Forecast"
          stroke={COLORS.predicted} strokeWidth={2.5}
          fill="url(#predGrad)"
          dot={false} connectNulls={false}
        />

        {/* "Now" reference line */}
        {splitIdx > 0 && splitIdx < data.length && (
          <ReferenceLine
            x={data[splitIdx]?.time}
            stroke="rgba(255,255,255,0.2)"
            strokeDasharray="6 3"
            label={{ value: 'Now', fill: '#64748b', fontSize: 10, position: 'top' }}
          />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
