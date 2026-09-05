// src/components/ForecastChart.jsx
import {
  ResponsiveContainer, ComposedChart, Area, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine
} from 'recharts'

const fmtTime = (isoStr) => {
  try {
    return new Date(isoStr).toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: false })
  } catch { return isoStr?.substring(11, 16) || '' }
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-3 text-xs shadow-lg min-w-[160px]">
      <div className="text-gray-500 font-medium mb-1">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="flex justify-between gap-4" style={{ color: p.color }}>
          <span>{p.name}</span>
          <span className="font-bold">{p.value != null ? `${p.value.toFixed(0)} MW` : '—'}</span>
        </div>
      ))}
    </div>
  )
}

export default function ForecastChart({ forecastData = [], actualsData = [], forecast = [], actuals = [] }) {
  // Accept both prop naming styles
  const fc = forecastData.length ? forecastData : forecast
  const ac = actualsData.length  ? actualsData  : actuals

  const data = [
    ...ac.map(a => ({
      time: fmtTime(a.timestamp),
      actual: Math.round(a.actual_demand_mw),
      predicted: null,
    })),
    ...fc.map(f => ({
      time: fmtTime(f.timestamp),
      actual: null,
      predicted: Math.round(f.predicted_demand_mw),
    })),
  ]

  const splitIdx = ac.length

  return (
    <ResponsiveContainer width="100%" height={340}>
      <ComposedChart data={data} margin={{ top: 10, right: 10, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="predGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#14b8a6" stopOpacity={0.2}/>
            <stop offset="95%" stopColor="#14b8a6" stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} interval={Math.floor(data.length / 8)} />
        <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} tickLine={false} axisLine={false} tickFormatter={v => `${v}MW`} width={60} />
        <Tooltip content={<CustomTooltip />} />
        <Legend iconType="circle" iconSize={8} formatter={v => <span className="text-xs text-gray-500">{v}</span>} />
        <Line type="monotone" dataKey="actual" name="Actual Demand" stroke="#6366f1" strokeWidth={2} strokeDasharray="5 3" dot={false} connectNulls={false} />
        <Area type="monotone" dataKey="predicted" name="AI Forecast" stroke="#14b8a6" strokeWidth={2.5} fill="url(#predGrad)" dot={false} connectNulls={false} />
        {splitIdx > 0 && splitIdx < data.length && (
          <ReferenceLine x={data[splitIdx]?.time} stroke="#e2e8f0" strokeDasharray="6 3"
            label={{ value: 'Now', fill: '#94a3b8', fontSize: 10, position: 'top' }} />
        )}
      </ComposedChart>
    </ResponsiveContainer>
  )
}
