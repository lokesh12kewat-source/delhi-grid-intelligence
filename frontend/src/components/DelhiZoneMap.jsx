// src/components/DelhiZoneMap.jsx
// Realistic Delhi zone SVG map with animated pulse, gradient fills, and click panel

import { useState } from 'react'
import RiskBadge from './RiskBadge'

// More accurate Delhi zone boundaries (viewBox 0 0 520 540)
const ZONE_PATHS = {
  delhi_north: {
    label: 'North Delhi',
    sub: 'TPDDL · Pitampura, Rohini',
    labelPos: [248, 78],
    centroid: [248, 68],
    d: 'M 158,18 L 200,12 L 265,10 L 335,14 L 362,28 L 368,58 L 355,88 L 330,108 L 290,122 L 248,130 L 205,122 L 170,108 L 148,82 L 142,52 Z',
  },
  delhi_west: {
    label: 'West Delhi',
    sub: 'BRPL · Janakpuri, Dwarka',
    labelPos: [118, 210],
    centroid: [118, 200],
    d: 'M 142,52 L 170,108 L 180,130 L 182,215 L 168,272 L 128,288 L 82,260 L 58,200 L 62,140 L 78,100 Z',
  },
  delhi_central: {
    label: 'Central Delhi',
    sub: 'NDMC · Connaught Place',
    labelPos: [240, 188],
    centroid: [240, 178],
    d: 'M 205,122 L 248,130 L 290,122 L 310,162 L 294,220 L 248,236 L 205,220 L 185,178 Z',
  },
  delhi_east: {
    label: 'East Delhi',
    sub: 'BYPL · Shahdara, Preet Vihar',
    labelPos: [378, 192],
    centroid: [378, 182],
    d: 'M 310,112 L 380,100 L 422,120 L 438,162 L 430,230 L 385,262 L 330,272 L 294,240 L 294,220 L 310,162 L 290,122 Z',
  },
  delhi_new: {
    label: 'New Delhi',
    sub: 'NDMC · Lutyen\'s Zone',
    labelPos: [242, 262],
    centroid: [242, 254],
    d: 'M 205,220 L 248,236 L 294,220 L 308,255 L 282,278 L 240,282 L 208,268 Z',
  },
  delhi_south: {
    label: 'South Delhi',
    sub: 'BRPL · Hauz Khas, Saket',
    labelPos: [245, 380],
    centroid: [245, 370],
    d: 'M 128,288 L 168,272 L 182,268 L 208,268 L 240,282 L 282,278 L 308,272 L 330,272 L 385,292 L 408,332 L 395,405 L 358,445 L 295,462 L 225,462 L 160,438 L 118,385 L 108,330 Z',
  },
}

const RISK_CONFIG = {
  LOW:      { fill: '#d1fae5', stroke: '#059669', dot: '#059669', glow: '#10b981', label: 'Normal' },
  MEDIUM:   { fill: '#fef3c7', stroke: '#d97706', dot: '#f59e0b', glow: '#fbbf24', label: 'High Demand' },
  HIGH:     { fill: '#fee2e2', stroke: '#dc2626', dot: '#ef4444', glow: '#f87171', label: 'Critical' },
  CRITICAL: { fill: '#ede9fe', stroke: '#7c3aed', dot: '#8b5cf6', glow: '#a78bfa', label: 'Emergency' },
  DEFAULT:  { fill: '#f1f5f9', stroke: '#94a3b8', dot: '#94a3b8', glow: '#94a3b8', label: 'Unknown' },
}

function getRisk(level) { return RISK_CONFIG[level] || RISK_CONFIG.DEFAULT }

export default function DelhiZoneMap({ zones = [] }) {
  const [selected, setSelected] = useState(null)
  const [hovered, setHovered]   = useState(null)

  const zoneMap = {}
  zones.forEach(z => { zoneMap[z.zone_id] = z })

  const sel = selected ? zoneMap[selected] : null
  const selPath = selected ? ZONE_PATHS[selected] : null

  return (
    <div className="section-card">
      {/* Header */}
      <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
        <div>
          <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
            <span className="text-2xl">🗺️</span> Live Grid Map — Delhi NCR
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">Real-time demand & risk across DISCOM zones · Click any zone for details</p>
        </div>
        <div className="flex items-center gap-4">
          {Object.entries({ LOW: 'Normal', MEDIUM: 'High Demand', HIGH: 'Critical' }).map(([k, label]) => (
            <div key={k} className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="w-2.5 h-2.5 rounded-full" style={{ background: RISK_CONFIG[k].dot }} />
              {label}
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col lg:flex-row gap-5">
        {/* SVG Map */}
        <div className="flex-1">
          <svg viewBox="0 0 520 480" className="w-full max-w-lg mx-auto" style={{ filter: 'drop-shadow(0 8px 24px rgba(0,0,0,0.10))' }}>
            <defs>
              {/* Zone gradient fills */}
              {Object.entries(ZONE_PATHS).map(([id]) => {
                const data  = zoneMap[id]
                const risk  = data?.risk_level || 'DEFAULT'
                const cfg   = getRisk(risk)
                return (
                  <radialGradient key={id} id={`grad-${id}`} cx="50%" cy="40%" r="60%">
                    <stop offset="0%" stopColor={cfg.fill} stopOpacity="1" />
                    <stop offset="100%" stopColor={cfg.stroke} stopOpacity="0.25" />
                  </radialGradient>
                )
              })}
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
                <feMerge><feMergeNode in="coloredBlur"/><feMergeNode in="SourceGraphic"/></feMerge>
              </filter>
              <filter id="shadow">
                <feDropShadow dx="0" dy="2" stdDeviation="3" floodOpacity="0.15"/>
              </filter>
            </defs>

            {/* Map background */}
            <rect width="520" height="480" rx="16" fill="#f8fafc"/>
            {/* Subtle grid */}
            {[80,160,240,320,400].map(x => <line key={`v${x}`} x1={x} y1="0" x2={x} y2="480" stroke="#e2e8f0" strokeWidth="0.5" strokeDasharray="4,4"/>)}
            {[80,160,240,320,400].map(y => <line key={`h${y}`} x1="0" y1={y} x2="520" y2={y} stroke="#e2e8f0" strokeWidth="0.5" strokeDasharray="4,4"/>)}

            {/* Yamuna river */}
            <path d="M 408,18 C 420,70 435,140 438,210 C 440,270 432,340 418,410 C 410,440 400,462 392,475"
              stroke="#93c5fd" strokeWidth="10" fill="none" strokeLinecap="round" opacity="0.6"/>
            <path d="M 408,18 C 420,70 435,140 438,210 C 440,270 432,340 418,410 C 410,440 400,462 392,475"
              stroke="white" strokeWidth="4" fill="none" strokeLinecap="round" opacity="0.4"/>
            <text x="445" y="150" fontSize="9" fill="#60a5fa" transform="rotate(80,445,150)" opacity="0.8">Yamuna</text>

            {/* Zone polygons */}
            {Object.entries(ZONE_PATHS).map(([zoneId, shape]) => {
              const data = zoneMap[zoneId]
              const risk = data?.risk_level || 'DEFAULT'
              const cfg  = getRisk(risk)
              const isHov = hovered === zoneId
              const isSel = selected === zoneId

              return (
                <g key={zoneId}
                  onClick={() => setSelected(isSel ? null : zoneId)}
                  onMouseEnter={() => setHovered(zoneId)}
                  onMouseLeave={() => setHovered(null)}
                  style={{ cursor: 'pointer' }}
                  filter={isSel ? 'url(#glow)' : 'url(#shadow)'}
                >
                  <path
                    d={shape.d}
                    fill={`url(#grad-${zoneId})`}
                    stroke={isSel ? '#0d9488' : isHov ? cfg.stroke : cfg.stroke}
                    strokeWidth={isSel ? 3 : isHov ? 2.5 : 1.5}
                    opacity={isHov || isSel ? 1 : 0.88}
                    style={{ transition: 'all 0.2s ease' }}
                  />
                  {/* Animated pulse dot */}
                  <circle cx={shape.centroid[0]} cy={shape.centroid[1]} r="8" fill={cfg.dot} opacity="0.2">
                    <animate attributeName="r" values="6;12;6" dur="2.5s" repeatCount="indefinite"/>
                    <animate attributeName="opacity" values="0.3;0;0.3" dur="2.5s" repeatCount="indefinite"/>
                  </circle>
                  <circle cx={shape.centroid[0]} cy={shape.centroid[1]} r="5" fill={cfg.dot} opacity="0.9"/>

                  {/* Zone label */}
                  <text x={shape.labelPos[0]} y={shape.labelPos[1]} textAnchor="middle"
                    fontSize="10" fontWeight="700" fill={cfg.stroke}
                    style={{ pointerEvents: 'none', userSelect: 'none' }}>
                    {shape.label}
                  </text>
                  {/* Demand label */}
                  {data?.predicted_demand_mw && (
                    <text x={shape.labelPos[0]} y={shape.labelPos[1] + 13} textAnchor="middle"
                      fontSize="8.5" fill="#475569"
                      style={{ pointerEvents: 'none', userSelect: 'none' }}>
                      {data.predicted_demand_mw.toFixed(0)} MW
                    </text>
                  )}
                </g>
              )
            })}

            {/* Compass */}
            <g transform="translate(482,448)">
              <circle r="18" fill="white" stroke="#e2e8f0" strokeWidth="1.5" opacity="0.9"/>
              <polygon points="0,-12 4,-4 0,-6 -4,-4" fill="#0d9488"/>
              <polygon points="0,12 4,4 0,6 -4,4" fill="#94a3b8"/>
              <text textAnchor="middle" y="-14" fontSize="7" fontWeight="700" fill="#0d9488">N</text>
            </g>

            {/* Scale bar */}
            <g transform="translate(20,462)">
              <line x1="0" y1="0" x2="50" y2="0" stroke="#94a3b8" strokeWidth="2"/>
              <line x1="0" y1="-4" x2="0" y2="4" stroke="#94a3b8" strokeWidth="1.5"/>
              <line x1="50" y1="-4" x2="50" y2="4" stroke="#94a3b8" strokeWidth="1.5"/>
              <text x="25" y="-6" textAnchor="middle" fontSize="7" fill="#94a3b8">~15 km</text>
            </g>
          </svg>
        </div>

        {/* Detail Panel */}
        <div className="w-full lg:w-72 flex-shrink-0">
          {sel && selPath ? (
            <div className="bg-gradient-to-br from-teal-50 to-white rounded-2xl p-5 border border-teal-100 shadow-sm h-full">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <p className="text-xs text-teal-600 font-semibold uppercase tracking-wider">{sel.discom || 'DISCOM'}</p>
                  <h3 className="text-lg font-bold text-gray-800 mt-0.5">{selPath.label}</h3>
                  <p className="text-xs text-gray-400">{selPath.sub}</p>
                </div>
                <RiskBadge level={sel.risk_level} />
              </div>

              {/* Main stat */}
              <div className="bg-white rounded-xl p-4 border border-gray-100 mb-3 shadow-sm">
                <p className="text-xs text-gray-400 mb-1">Current Demand</p>
                <p className="text-3xl font-black text-gray-800">
                  {sel.predicted_demand_mw?.toFixed(0)}
                  <span className="text-sm font-normal text-gray-400 ml-1">MW</span>
                </p>
                <p className="text-xs text-gray-400 mt-1">Capacity: {sel.capacity_mw?.toFixed(0)} MW</p>
              </div>

              {/* Stats grid */}
              <div className="grid grid-cols-2 gap-2 mb-3">
                <div className="bg-white rounded-xl p-3 border border-gray-100">
                  <p className="text-xs text-gray-400">Utilization</p>
                  <p className="text-lg font-bold text-gray-700">{sel.utilization_pct?.toFixed(1)}%</p>
                </div>
                <div className="bg-white rounded-xl p-3 border border-gray-100">
                  <p className="text-xs text-gray-400">Headroom</p>
                  <p className="text-lg font-bold text-gray-700">{sel.headroom_mw?.toFixed(0)} MW</p>
                </div>
              </div>

              {/* Utilization bar */}
              <div className="mb-3">
                <div className="flex justify-between text-xs text-gray-400 mb-1.5">
                  <span>Grid Load</span>
                  <span className="font-medium">{sel.utilization_pct?.toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                  <div className="h-3 rounded-full transition-all duration-700"
                    style={{
                      width: `${Math.min(sel.utilization_pct || 0, 100)}%`,
                      background: sel.utilization_pct > 90
                        ? 'linear-gradient(90deg,#f87171,#ef4444)'
                        : sel.utilization_pct > 75
                          ? 'linear-gradient(90deg,#fbbf24,#f59e0b)'
                          : 'linear-gradient(90deg,#34d399,#059669)',
                    }}
                  />
                </div>
              </div>

              <button onClick={() => setSelected(null)}
                className="w-full text-xs text-gray-400 hover:text-teal-600 border border-gray-200 hover:border-teal-300 rounded-lg py-2 transition-all">
                ✕ Close panel
              </button>
            </div>
          ) : (
            <div className="bg-gradient-to-br from-slate-50 to-white rounded-2xl p-5 border border-gray-100 h-full">
              <p className="text-sm font-semibold text-gray-600 mb-1">Zone Overview</p>
              <p className="text-xs text-gray-400 mb-4">Click a zone on the map for details</p>
              <div className="space-y-2">
                {zones.slice(0, 6).map(z => {
                  const cfg = getRisk(z.risk_level)
                  const path = ZONE_PATHS[z.zone_id]
                  return (
                    <div key={z.zone_id} onClick={() => setSelected(z.zone_id)}
                      className="flex items-center justify-between px-3 py-2.5 bg-white rounded-xl border border-gray-100 hover:border-teal-200 hover:shadow-sm cursor-pointer transition-all group">
                      <div className="flex items-center gap-2.5">
                        <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: cfg.dot }}/>
                        <div>
                          <p className="text-xs font-semibold text-gray-700 group-hover:text-teal-700">{path?.label || z.zone_id}</p>
                          <p className="text-xs text-gray-400">{z.predicted_demand_mw?.toFixed(0)} MW</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-gray-100 rounded-full h-1.5">
                          <div className="h-1.5 rounded-full" style={{ width: `${Math.min(z.utilization_pct||0,100)}%`, background: cfg.dot }}/>
                        </div>
                        <span className="text-xs text-gray-500">{z.utilization_pct?.toFixed(0)}%</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
