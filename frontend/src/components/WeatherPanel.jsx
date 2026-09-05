export default function WeatherPanel({ weather = {}, zoneWeather = {} }) {
  const zones = Object.entries(zoneWeather || {})

  return (
    <div className="space-y-4">
      {/* City average */}
      <div className="flex gap-4">
        <div className="flex-1 bg-gradient-to-br from-sky-50 to-blue-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">Delhi Avg Temp</p>
          <p className="text-2xl font-bold text-gray-800">
            {weather.temperature_c != null ? Math.round(weather.temperature_c) : '—'}°C
          </p>
        </div>
        <div className="flex-1 bg-gradient-to-br from-teal-50 to-cyan-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">Humidity</p>
          <p className="text-2xl font-bold text-gray-800">{weather.humidity_pct ?? '—'}%</p>
        </div>
      </div>

      {/* Zone breakdown */}
      {zones.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {zones.slice(0,6).map(([zone, w]) => (
            <div key={zone} className="bg-gray-50 rounded-lg px-3 py-2">
              <p className="text-xs text-gray-500 capitalize">{zone.replace('delhi_','').replace('_',' ')}</p>
              <p className="text-sm font-semibold text-gray-800">
                {w.temperature_c != null ? Math.round(w.temperature_c) : '—'}°C
                {w.humidity_pct != null && <span className="text-gray-400 font-normal ml-1">· {w.humidity_pct}%</span>}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
