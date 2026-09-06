// src/components/DelhiZoneMap.jsx
// SVG-based interactive map of Delhi zones — no external map library needed

import { useState } from 'react'
import RiskBadge from './RiskBadge'

// Approximate SVG paths for Delhi's 6 zones (viewBox 0 0 500 520)
const ZONE_PATHS = {
  delhi_north: {
    label: 'North Delhi',
    labelPos: [235, 72],
    d: 'M 170,15 L 335,15 L 355,65 L 325,110 L 280,128 L 220,128 L 175,110 L 148,65 Z',
  },
  delhi_west: {
    label: 'West Delhi',
    labelPos: [130, 195],
    d: 'M 148,65 L 175,110 L 188,135 L 192,215 L 178,270 L 135,282 L 88,250 L 68,185 L 80,110 Z',
  },
  delhi_central: {
    label: 'Central Delhi',
    labelPos: [238, 178],
    d: 'M 188,135 L 220,128 L 280,128 L 298,168 L 280,218 L 232,232 L 200,218 L 188,178 Z',
  },
  delhi_east: {
    label: 'East Delhi',
    labelPos: [360, 185],
    d: 'M 298,118 L 385,108 L 415,158 L 405,238 L 345,265 L 295,235 L 278,185 L 280,128 L 325,110 Z',
  },
  delhi_new: {
    label: 'New Delhi',
    labelPos: [235, 260],
    d: 'M 200,218 L 280,218 L 292,255 L 265,278 L 222,272 L 200,252 Z',
  },
  delhi_south: {
    label: 'South Delhi',
    labelPos: [238, 365],
    d: 'M 135,282 L 178,270 L 200,252 L 222,272 L 265,278 L 295,265 L 345,282 L 375,325 L 360,400 L 290,438 L 215,442 L 148,405 L 108,340 Z',
  },
}

const RISK_COLORS = {
  LOW:      { fill: '#bbf7d0', stroke: '#16a34a', dot: '#16a34a', text: 'text-green-700'  },
  MEDIUM:   { fill: '#fde68a', stroke: '#d97706', dot: '#d97706', text: 'text-amber-700'  },
  HIGH:     { fill: '#fecaca', stroke: '#dc2626', dot: '#ef4444', text: 'text-red-700'    },
  CRITICAL: { fill: '#ddd6fe', stroke: '#7c3aed', dot: '#7c3aed', text: 'text-purple-700' },
  DEFAULT:  { fill: '#e2e8f0', stroke: '#94a3b8', dot: '#94a3b8', text: 'text-gray-500'  },
}

function getRiskStyle(level) {
  return RISK_COLORS[level] || RISK_COLORS.DEFAULT
}

export default function DelhiZoneMap({ zones = [] }) {
  const [hoveredZone, setHoveredZone] = useState(null)
  const [selectedZone, setSelectedZone] = useState(null)

  // Build a lookup by zone_id
  const zoneMap = {}
  zones.forEach(z => { zoneMap[z.zone_id] = z })

  const selectedData = selectedZone ? zoneMap[selectedZone] : null

  return (
    <div className="section-card">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <div>
          <h2 className="text-lg font-semibold text-gray-800">Live Grid Map — Delhi</h2>
          <p className="text-xs text-gray-400">Real-time demand &amp; risk by DISCOM zone · Click a zone for details</p>
        </div>
        {/* Legend */}
        <div className="flex items-center gap-3 flex-wrap">
          {[
            { label: 'Normal',      color: '#16a34a' },
            { label: 'High Demand', color: '#d97706' },
            { label: 'Critical',    color: '#7c3aed' },
          ].map(({ label, color }) => (
            <div key={label} className="flex items-center gap-1.5 text-xs text-gray-500">
              <span className="w-3 h-3 rounded-full inline-block" style={{ background: color }} />
              {label}
            </div>
          ))}
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-4">
        {/* SVG Map */}
        <div className="flex-1 min-w-0">
          <svg
            viewBox="0 0 500 465"
            className="w-full max-w-md mx-auto"
            style={{ filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.08))' }}
          >
            {/* Map background */}
            <rect width="500" height="465" rx="12" fill="#f8fafc" />

            {/* Grid lines for map feel */}
            {[100,200,300,400].map(x => (
              <line key={`v${x}`} x1={x} y1="0" x2={x} y2="465" stroke="#e2e8f0" strokeWidth="0.5" />
            ))}
            {[100,200,300,400].map(y => (
              <line key={`h${y}`} x1="0" y1={y} x2="500" y2={y} stroke="#e2e8f0" strokeWidth="0.5" />
            ))}

            {/* Yamuna river (stylized) */}
            <path
              d="M 370,10 C 380,80 395,150 405,220 C 410,280 400,350 385,420"
              stroke="#bfdbfe" strokeWidth="8" fill="none" strokeLinecap="round" opacity="0.7"
            />
            <text x="392" y="100" fontSize="8" fill="#93c5fd" textAnchor="middle" transform="rotate(80,392,100)">Yamuna</text>

            {/* Zone polygons */}
            {Object.entries(ZONE_PATHS).map(([zoneId, shape]) => {
              const data      = zoneMap[zoneId]
              const risk      = data?.risk_level || 'DEFAULT'
              const style     = getRiskStyle(risk)
              const isHovered = hoveredZone === zoneId
              const isSelected= selectedZone === zoneId

              return (
                <g key={zoneId}
                  onClick={() => setSelectedZone(isSelected ? null : zoneId)}
                  onMouseEnter={() => setHoveredZone(zoneId)}
                  onMouseLeave={() => setHoveredZone(null)}
                  style={{ cursor: 'pointer' }}
                >
                  <path
                    d={shape.d}
                    fill={style.fill}
                    stroke={isSelected ? '#0d9488' : style.stroke}
                    strokeWidth={isSelected ? 2.5 : isHovered ? 2 : 1.5}
                    opacity={isHovered ? 0.95 : 0.85}
                    style={{ transition: 'all 0.15s ease' }}
                  />

                  {/* Zone label */}
                  <text
                    x={shape.labelPos[0]}
                    y={shape.labelPos[1]}
                    textAnchor="middle"
                    fontSize="10"
                    fontWeight="600"
                    fill={style.stroke}
                    style={{ pointerEvents: 'none', userSelect: 'none' }}
                  >
                    {shape.label}
                  </text>

                  {/* Demand label */}
                  {data?.predicted_demand_mw && (
                    <text
                      x={shape.labelPos[0]}
                      y={shape.labelPos[1] + 13}
                      textAnchor="middle"
                      fontSize="9"
                      fill="#475569"
                      style={{ pointerEvents: 'none', userSelect: 'none' }}
                    >
                      {data.predicted_demand_mw.toFixed(0)} MW
                    </text>
                  )}

                  {/* Risk dot */}
                  <circle
                    cx={shape.labelPos[0]}
                    cy={shape.labelPos[1] - 16}
                    r="5"
                    fill={style.dot}
                    opacity="0.9"
                  />
                </g>
              )
            })}

            {/* Compass */}
            <g transform="translate(460,440)">
              <circle r="14" fill="white" stroke="#e2e8f0" strokeWidth="1" />
              <text textAnchor="middle" y="-3" fontSize="8" fontWeight="700" fill="#475569">N</text>
              <line x1="0" y1="0" x2="0" y2="-8" stroke="#475569" strokeWidth="1.5" />
            </g>
          </svg>
        </div>

        {/* Detail Panel */}
        <div className="w-full md:w-60 flex-shrink-0">
          {selectedData ? (
            <div className="bg-gray-50 rounded-xl p-4 border border-gray-100 h-full">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <p className="text-xs text-teal-600 font-semibold uppercase tracking-wider">{selectedData.discom || 'DISCOM'}</p>
                  <h3 className="text-base font-bold text-gray-800 mt-0.5">
                    {ZONE_PATHS[selectedZone]?.label}
                  </h3>
                </div>
                <RiskBadge level={selectedData.risk_level} />
              </div>

              <div className="space-y-3">
                <div className="bg-white rounded-lg p-3 border border-gray-100">
                  <p className="text-xs text-gray-400 mb-0.5">Current Demand</p>
                  <p className="text-xl font-bold text-gray-800">
                    {selectedData.predicted_demand_mw?.toFixed(0)}
                    <span className="text-xs font-normal text-gray-400 ml-1">MW</span>
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="bg-white rounded-lg p-2.5 border border-gray-100">
                    <p className="text-xs text-gray-400">Utilization</p>
                    <p className="text-sm font-bold text-gray-700">{selectedData.utilization_pct?.toFixed(1)}%</p>
                  </div>
                  <div className="bg-white rounded-lg p-2.5 border border-gray-100">
                    <p className="text-xs text-gray-400">Headroom</p>
                    <p className="text-sm font-bold text-gray-700">{selectedData.headroom_mw?.toFixed(0)} MW</p>
                  </div>
                </div>

                {/* Utilization bar */}
                <div>
                  <div className="flex justify-between text-xs text-gray-400 mb-1">
                    <span>Grid Load</span>
                    <span>{selectedData.utilization_pct?.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="h-2 rounded-full transition-all"
                      style={{
                        width: `${Math.min(selectedData.utilization_pct || 0, 100)}%`,
                        background: selectedData.utilization_pct > 90 ? '#ef4444'
                          : selectedData.utilization_pct > 75 ? '#f59e0b' : '#14b8a6'
                      }}
                    />
                  </div>
                </div>

                <p className="text-xs text-gray-400 italic">{selectedData.capacity_note}</p>
              </div>

              <button
                onClick={() => setSelectedZone(null)}
                className="mt-3 text-xs text-gray-400 hover:text-gray-600 underline"
              >
                Close panel
              </button>
            </div>
          ) : (
            <div className="bg-gray-50 rounded-xl p-6 border border-gray-100 h-full flex flex-col items-center justify-center text-center">
              <div className="text-3xl mb-2">🗺️</div>
              <p className="text-sm text-gray-400">Click any zone on the map to see demand details</p>
              <div className="mt-4 space-y-1 w-full">
                {zones.slice(0,6).map(z => (
                  <div
                    key={z.zone_id}
                    onClick={() => setSelectedZone(z.zone_id)}
                    className="flex items-center justify-between text-xs px-3 py-1.5 bg-white rounded-lg border border-gray-100 cursor-pointer hover:border-teal-300 transition-all"
                  >
                    <span className="text-gray-600 font-medium">{ZONE_PATHS[z.zone_id]?.label || z.zone_id}</span>
                    <RiskBadge level={z.risk_level} />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
