// src/components/WeatherPanel.jsx
import { Thermometer, Droplets, Wind } from 'lucide-react'

export function WeatherPanel({ weather, zones = [] }) {
  const avgTemp = weather?.delhi_avg_temp
  const maxTemp = weather?.delhi_max_temp
  const minTemp = weather?.delhi_min_temp
  const spread  = weather?.delhi_temp_spread
  const hum     = weather?.delhi_avg_humidity

  return (
    <div className="glass-card p-5">
      <div className="section-title">
        <span>🌤️</span> Delhi Weather
        <span className="ml-auto text-[10px] text-slate-600 font-normal">Open-Meteo · 6 zones</span>
      </div>

      {/* Main metrics */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        <div className="text-center">
          <div className="text-3xl font-extrabold text-cyber-cyan">
            {avgTemp != null ? `${avgTemp.toFixed(1)}°` : '—'}
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wide">Avg Temp</div>
        </div>
        <div className="text-center border-x border-white/[0.06]">
          <div className="text-xl font-bold text-white">
            {maxTemp != null ? `${maxTemp.toFixed(0)}°` : '—'}
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wide">Max</div>
          <div className="text-xl font-bold text-cyber-blue mt-1">
            {minTemp != null ? `${minTemp.toFixed(0)}°` : '—'}
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wide">Min</div>
        </div>
        <div className="text-center">
          <div className="flex items-center justify-center gap-1 text-xl font-bold text-cyber-blue">
            <Droplets size={14} />
            {hum != null ? `${hum.toFixed(0)}%` : '—'}
          </div>
          <div className="text-[10px] text-slate-500 uppercase tracking-wide">Humidity</div>
          {spread != null && (
            <>
              <div className="text-lg font-bold text-cyber-yellow mt-1">{spread.toFixed(1)}°</div>
              <div className="text-[10px] text-slate-500 uppercase tracking-wide">Spread</div>
            </>
          )}
        </div>
      </div>

      {/* Zone temperature dots */}
      {zones.length > 0 && (
        <div className="space-y-1.5">
          <div className="text-[10px] text-slate-600 uppercase tracking-widest mb-2">Zone Temperatures</div>
          {zones.map(z => (
            <div key={z.zone_id} className="flex items-center justify-between text-xs">
              <span className="text-slate-500">{z.zone_name?.replace(' Delhi', '').replace(' (', '\n(')}</span>
              <div className="flex items-center gap-3">
                {z.humidity_pct != null && (
                  <span className="text-cyber-blue text-[10px]">{z.humidity_pct.toFixed(0)}%</span>
                )}
                <span className={`font-bold ${
                  z.temperature_c > 40 ? 'text-cyber-red' :
                  z.temperature_c > 35 ? 'text-cyber-yellow' :
                  z.temperature_c > 28 ? 'text-cyber-orange' : 'text-cyber-green'
                }`}>
                  {z.temperature_c != null ? `${z.temperature_c.toFixed(1)}°C` : '—'}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-3 pt-3 border-t border-white/[0.04] text-[9px] text-slate-600">
        Source: Open-Meteo API · 6 Delhi locations · IST timezone
      </div>
    </div>
  )
}
