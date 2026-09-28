// src/components/ForecastChart.jsx
// Animated area + line chart with gradients, tooltips, and reference lines

import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, ReferenceLine, Dot
} from 'recharts'
import { format, parseISO } from 'date-fns'

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white/95 backdrop-blur border border-gray-100 rounded-xl shadow-xl px-4 py-3 text-sm">
      <p className="font-semibold text-gray-700 mb-2 text-xs uppercase tracking-wider">
        {label}
      </p>
      {payload.map((p, i) => (
        <div key={i} className="flex items-center gap-2 mb-1">
          <span className="w-3 h-3 rounded-full flex-shrink-0" style={{ background: p.color }}/>
          <span className="text-gray-500 text-xs">{p.name}:</span>
          <span className="font-bold text-gray-800">{Number(p.value).toFixed(0)} MW</span>
        </div>
      ))}
    </div>
  )
}

const CustomDot = (props) => {
  const { cx, cy, payload } = props
  const risk = payload?.risk_level
  const color = risk === 'HIGH' || risk === 'CRITICAL' ? '#ef4444'
    : risk === 'MEDIUM' ? '#f59e0b' : '#14b8a6'
  if (!cx || !cy) return null
  return <circle cx={cx} cy={cy} r={4} fill={color} stroke="white" strokeWidth={2}/>
}

export default function ForecastChart({ forecast = [], actuals = [] }) {
  if (!forecast.length && !actuals.length) return null

  // Merge actuals + forecast into one timeline
  const actualMap = {}
  actuals.forEach(a => {
    const key = a.timestamp?.substring(0, 13)
    if (key) actualMap[key] = a.actual_demand_mw
  })

  const chartData = forecast.slice(0, 24).map(f => {
    const key  = f.timestamp?.substring(0, 13)
    const time = f.timestamp
      ? format(parseISO(f.timestamp), 'HH:mm')
      : '??:??'
    return {
      time,
      forecast: Math.round(f.predicted_demand_mw ?? 0),
      actual:   actualMap[key] ? Math.round(actualMap[key]) : undefined,
      risk_level: f.risk_level,
    }
  })

  // Compute Y-axis domain with some padding
  const allVals = chartData.flatMap(d => [d.forecast, d.actual].filter(Boolean))
  const minY = Math.max(0, Math.min(...allVals) - 300)
  const maxY = Math.max(...allVals) + 400

  // Avg demand for reference line
  const avgDemand = Math.round(allVals.reduce((a, b) => a + b, 0) / allVals.length)

  return (
    <div className="section-card">
      <div className="flex items-center justify-between mb-5 flex-wrap gap-2">
        <div>
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <span className="text-2xl">📈</span> 24-Hour Demand Forecast
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">AI-predicted demand vs actual load · Hover for details</p>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <div className="flex items-center gap-1.5">
            <span className="w-6 h-0.5 bg-teal-500 rounded block"/>
            Forecast
          </div>
          {actuals.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="w-6 h-0.5 bg-blue-400 rounded block" style={{ borderTop: '2px dashed' }}/>
              Actual
            </div>
          )}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="forecastGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#14b8a6" stopOpacity={0.35}/>
              <stop offset="95%" stopColor="#14b8a6" stopOpacity={0.02}/>
            </linearGradient>
            <linearGradient id="actualGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%"  stopColor="#60a5fa" stopOpacity={0.25}/>
              <stop offset="95%" stopColor="#60a5fa" stopOpacity={0.02}/>
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="4 4" stroke="#f0f4f8" vertical={false}/>

          <XAxis dataKey="time" tick={{ fontSize: 11, fill: '#94a3b8' }}
            tickLine={false} axisLine={{ stroke: '#e2e8f0' }}
            interval={Math.floor(chartData.length / 6)}/>

          <YAxis domain={[minY, maxY]} tick={{ fontSize: 11, fill: '#94a3b8' }}
            tickLine={false} axisLine={false}
            tickFormatter={v => `${(v/1000).toFixed(1)}k`}
            width={45}/>

          <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#0d9488', strokeWidth: 1.5, strokeDasharray: '4 2' }}/>

          {/* Reference line for average */}
          <ReferenceLine y={avgDemand} stroke="#94a3b8" strokeDasharray="6 3"
            label={{ value: `Avg ${avgDemand} MW`, fill: '#94a3b8', fontSize: 10, position: 'insideTopRight' }}/>

          {/* Actual demand */}
          {actuals.length > 0 && (
            <Area type="monotone" dataKey="actual" name="Actual"
              stroke="#60a5fa" strokeWidth={2} strokeDasharray="5 3"
              fill="url(#actualGrad)"
              dot={false} animationDuration={800} animationBegin={0}/>
          )}

          {/* Forecast */}
          <Area type="monotone" dataKey="forecast" name="Forecast"
            stroke="#14b8a6" strokeWidth={2.5}
            fill="url(#forecastGrad)"
            dot={<CustomDot/>}
            activeDot={{ r: 7, fill: '#0d9488', stroke: 'white', strokeWidth: 2 }}
            animationDuration={1200} animationBegin={100}/>
        </AreaChart>
      </ResponsiveContainer>

      {/* Risk mini-bar below chart */}
      <div className="mt-3 flex gap-0.5 rounded-full overflow-hidden h-2">
        {chartData.map((d, i) => {
          const bg = d.risk_level === 'CRITICAL' ? '#8b5cf6'
            : d.risk_level === 'HIGH' ? '#ef4444'
            : d.risk_level === 'MEDIUM' ? '#f59e0b' : '#10b981'
          return <div key={i} className="flex-1 transition-all" style={{ background: bg }}
            title={`${d.time}: ${d.risk_level}`}/>
        })}
      </div>
      <p className="text-xs text-gray-400 mt-1 text-center">Risk level timeline</p>
    </div>
  )
}
