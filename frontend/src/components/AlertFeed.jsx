export default function AlertFeed({ alerts = [] }) {
  if (!alerts.length) {
    return (
      <div className="flex items-center gap-3 py-6 justify-center text-gray-400">
        <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
          <span className="text-green-500 text-lg">✓</span>
        </div>
        <span className="text-sm">No active alerts — grid operating normally</span>
      </div>
    )
  }

  const severityStyle = {
    CRITICAL: { border: 'border-l-4 border-red-400',    bg: 'bg-red-50',    text: 'text-red-700',    badge: 'bg-red-100 text-red-700'    },
    HIGH:     { border: 'border-l-4 border-orange-400', bg: 'bg-orange-50', text: 'text-orange-700', badge: 'bg-orange-100 text-orange-700'},
    MEDIUM:   { border: 'border-l-4 border-yellow-400', bg: 'bg-yellow-50', text: 'text-yellow-700', badge: 'bg-yellow-100 text-yellow-700'},
    LOW:      { border: 'border-l-4 border-blue-300',   bg: 'bg-blue-50',   text: 'text-blue-700',   badge: 'bg-blue-100 text-blue-700'   },
  }

  return (
    <div className="space-y-3">
      {alerts.map((a, i) => {
        const s = severityStyle[a.severity] || severityStyle.LOW
        return (
          <div key={i} className={`rounded-xl p-4 ${s.bg} ${s.border}`}>
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className={`inline-block text-xs font-semibold px-2 py-0.5 rounded-full mb-1 ${s.badge}`}>
                  {a.severity}
                </span>
                <p className={`text-sm font-medium ${s.text}`}>{a.message}</p>
                <p className="text-xs text-gray-500 mt-0.5">{a.zone} · {a.timestamp?.slice(11,16) ?? ''}</p>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
