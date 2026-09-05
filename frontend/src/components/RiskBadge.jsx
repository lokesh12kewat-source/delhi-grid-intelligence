export default function RiskBadge({ level }) {
  const styles = {
    LOW:      'risk-low',
    MEDIUM:   'risk-medium',
    HIGH:     'risk-high',
    CRITICAL: 'risk-critical',
  }
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${styles[level] || 'risk-low'}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {level || 'LOW'}
    </span>
  )
}
