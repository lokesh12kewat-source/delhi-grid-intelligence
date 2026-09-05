export default function WeatherPanel({ weather = {}, zoneWeather = {} }) {
  const temp     = weather.delhi_avg_temp
  const humidity = weather.delhi_avg_humidity
  const zones    = Array.isArray(weather.zones) ? weather.zones : []

  return (
    <div className="space-y-4">
      <div className="flex gap-4">
        <div className="flex-1 bg-gradient-to-br from-sky-50 to-blue-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">Delhi Avg Temp</p>
          <p className="text-2xl font-bold text-gray-800">
            {temp != null ? Math.round(temp) : '—'}°C
          </p>
        </div>
        <div className="flex-1 bg-gradient-to-br from-teal-50 to-cyan-50 rounded-xl p-4">
          <p className="text-xs text-gray-500 mb-1">Humidity</p>
          <p className="text-2xl font-bold text-gray-800">{humidity ?? '—'}%</p>
        </div>
      </div>

      {/* Source note */}
      {weather.data_note && (
        <p className="text-xs text-gray-400 italic">{weather.data_note}</p>
      )}

      {/* Zone weather breakdown if available */}
      {zones.length > 0 && (
        <div className="grid grid-cols-2 gap-2">
          {zones.slice(0,6).map((z, i) => (
            <div key={i} className="bg-gray-50 rounded-lg px-3 py-2">
              <p className="text-xs text-gray-500 capitalize">
                {(z.zone_id || z.zone || '').replace('delhi_','').replace('_',' ')}
              </p>
              <p className="text-sm font-semibold text-gray-800">
                {z.temperature_c != null ? Math.round(z.temperature_c) : '—'}°C
                {z.humidity_pct != null && (
                  <span className="text-gray-400 font-normal ml-1">· {z.humidity_pct}%</span>
                )}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
