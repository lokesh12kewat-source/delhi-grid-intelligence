export default function RecommendationPanel({ data }) {
  if (!data || !data.risk_level) return (
    <div className="flex items-center justify-center py-8 text-gray-400 text-sm">
      Loading AI recommendation...
    </div>
  )

  const riskColors = {
    LOW:      { bg: 'bg-green-50',  border: 'border-green-200', text: 'text-green-700',  badge: 'bg-green-100 text-green-800'  },
    MEDIUM:   { bg: 'bg-yellow-50', border: 'border-yellow-200',text: 'text-yellow-700', badge: 'bg-yellow-100 text-yellow-800' },
    HIGH:     { bg: 'bg-red-50',    border: 'border-red-200',   text: 'text-red-700',    badge: 'bg-red-100 text-red-800'      },
    CRITICAL: { bg: 'bg-purple-50', border: 'border-purple-200',text: 'text-purple-700', badge: 'bg-purple-100 text-purple-800'},
  }
  const c = riskColors[data.risk_level] || riskColors.LOW

  // API uses action_text or summary or llm_explanation
  const message = data.action_text || data.summary || data.llm_explanation || ''
  const steps   = data.structured_steps || []

  return (
    <div className="space-y-4">
      <div className={`rounded-xl p-4 border ${c.bg} ${c.border}`}>
        <div className="flex items-center justify-between mb-2 flex-wrap gap-2">
          <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${c.badge}`}>
            {data.risk_level} RISK
          </span>
          {data.action_code && (
            <span className={`text-xs font-semibold ${c.text}`}>{data.action_code}</span>
          )}
        </div>
        <p className={`text-sm ${c.text}`}>{message}</p>
      </div>

      {/* Demand drivers */}
      {data.demand_drivers && (
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(data.demand_drivers).map(([k, v]) => (
            <div key={k} className="bg-gray-50 rounded-lg px-3 py-2">
              <p className="text-xs text-gray-400 capitalize">{k.replace('_', ' ')}</p>
              <p className="text-sm font-semibold text-gray-700">{v}</p>
            </div>
          ))}
        </div>
      )}

      {steps.length > 0 && (
        <div className="space-y-2">
          {steps.map((step, i) => (
            <div key={i} className="flex items-start gap-2 text-sm text-gray-600">
              <span className="w-5 h-5 rounded-full bg-teal-100 text-teal-700 flex items-center justify-center text-xs font-bold flex-shrink-0 mt-0.5">
                {i + 1}
              </span>
              <span>{step}</span>
            </div>
          ))}
        </div>
      )}

      <p className="text-xs text-gray-400 flex items-center gap-1">
        <span className="w-3 h-3 rounded-full bg-teal-400 inline-block" />
        Powered by Gemini AI
      </p>
    </div>
  )
}
