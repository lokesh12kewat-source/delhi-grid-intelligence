// src/components/RecommendationPanel.jsx
import { Sparkles, AlertTriangle, Info } from 'lucide-react'

const ACTION_ICON = {
  MONITOR:   '🟢',
  PREPARE:   '🟡',
  ALERT:     '🟠',
  EMERGENCY: '🔴',
}

const ACTION_COLOR = {
  MONITOR:   'border-cyber-green/30 bg-cyber-green/[0.04]',
  PREPARE:   'border-cyber-yellow/30 bg-cyber-yellow/[0.04]',
  ALERT:     'border-[#ff6600]/30 bg-[#ff6600]/[0.04]',
  EMERGENCY: 'border-cyber-red/30 bg-cyber-red/[0.04]',
}

export function RecommendationPanel({ recommendation }) {
  if (!recommendation) {
    return (
      <div className="glass-card p-5 animate-pulse">
        <div className="h-4 bg-white/[0.06] rounded w-1/3 mb-3" />
        <div className="h-3 bg-white/[0.04] rounded w-full mb-2" />
        <div className="h-3 bg-white/[0.04] rounded w-4/5" />
      </div>
    )
  }

  const code = recommendation.action_code || 'MONITOR'
  const cardCls = ACTION_COLOR[code] || ACTION_COLOR.MONITOR

  return (
    <div className={`glass-card p-5 border ${cardCls}`}>
      <div className="section-title">
        <Sparkles size={14} className="text-cyber-cyan" />
        AI Recommendation
        <span className="ml-auto text-[10px] text-slate-500 font-normal">Gemini · LLM-enhanced</span>
      </div>

      {/* Action code badge */}
      <div className="flex items-center gap-2 mb-4">
        <span className="text-xl">{ACTION_ICON[code] || '⚪'}</span>
        <span className="text-sm font-bold text-white uppercase tracking-widest">{code}</span>
        <span className="text-xs text-slate-500">— {recommendation.risk_level} Risk</span>
      </div>

      {/* LLM explanation */}
      {recommendation.llm_explanation && (
        <p className="text-sm text-slate-300 leading-relaxed mb-4 italic">
          "{recommendation.llm_explanation}"
        </p>
      )}

      {/* Structured data grid */}
      <div className="grid grid-cols-2 gap-3 text-xs">
        {recommendation.peak_time && (
          <div>
            <div className="text-slate-500 mb-0.5">Peak Hour</div>
            <div className="font-semibold text-white">{recommendation.peak_time}</div>
          </div>
        )}
        {recommendation.peak_demand_mw != null && (
          <div>
            <div className="text-slate-500 mb-0.5">Peak Demand</div>
            <div className="font-semibold text-white">{recommendation.peak_demand_mw.toFixed(0)} MW</div>
          </div>
        )}
        {recommendation.headroom_mw != null && (
          <div>
            <div className="text-slate-500 mb-0.5">Grid Headroom</div>
            <div className="font-semibold text-cyber-cyan">{recommendation.headroom_mw.toFixed(0)} MW</div>
          </div>
        )}
        {recommendation.utilization_pct != null && (
          <div>
            <div className="text-slate-500 mb-0.5">Grid Utilization</div>
            <div className="font-semibold text-white">{recommendation.utilization_pct.toFixed(1)}%</div>
          </div>
        )}
      </div>

      {/* Weather drivers */}
      {recommendation.demand_drivers && (
        <div className="mt-4 pt-3 border-t border-white/[0.05]">
          <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-2">Demand Drivers</div>
          <div className="flex flex-wrap gap-2">
            {Object.entries(recommendation.demand_drivers).map(([k, v]) => (
              <div key={k} className="text-[10px] bg-white/[0.04] px-2 py-1 rounded-full">
                <span className="text-slate-500">{k.replace(/_/g, ' ')}: </span>
                <span className="text-slate-300">{v}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="mt-3 pt-2 border-t border-white/[0.04] text-[9px] text-slate-600">
        Capacity thresholds are demo/configurable — not official SLDC limits
      </div>
    </div>
  )
}
