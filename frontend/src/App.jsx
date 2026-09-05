import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Zap, Search, Activity } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import ForecastView from './pages/ForecastView'
import ZoneAnalysis from './pages/ZoneAnalysis'
import Alerts from './pages/Alerts'

export default function App() {
  return (
    <BrowserRouter>
      {/* ── Navbar ── */}
      <nav className="navbar sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-14 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center">
              <Zap size={16} className="text-white" />
            </div>
            <span className="font-bold text-gray-800 text-base">Delhi Grid AI</span>
          </div>

          {/* Nav links */}
          <div className="flex items-center gap-1">
            {[
              { to: '/',        label: 'Dashboard'    },
              { to: '/forecast',label: 'Forecast'     },
              { to: '/zones',   label: 'Zone Analysis'},
              { to: '/alerts',  label: 'Alerts'       },
            ].map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `px-4 py-1.5 rounded-full text-sm font-medium transition-all ${
                    isActive
                      ? 'bg-teal-500 text-white shadow-sm'
                      : 'text-gray-600 hover:bg-gray-100'
                  }`
                }
              >
                {label}
              </NavLink>
            ))}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 bg-gray-100 rounded-full px-3 py-1.5">
              <Search size={13} className="text-gray-400" />
              <span className="text-xs text-gray-400">Search...</span>
            </div>
            <div className="flex items-center gap-1.5 bg-green-50 border border-green-200 rounded-full px-3 py-1.5">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs font-medium text-green-700">Live Grid</span>
            </div>
          </div>
        </div>
      </nav>

      {/* ── Pages ── */}
      <Routes>
        <Route path="/"        element={<Dashboard />} />
        <Route path="/forecast"element={<ForecastView />} />
        <Route path="/zones"   element={<ZoneAnalysis />} />
        <Route path="/alerts"  element={<Alerts />} />
      </Routes>

      {/* ── Footer ── */}
      <footer className="text-center py-6 text-xs text-gray-400 border-t border-gray-100 mt-8">
        Delhi Grid Intelligence · AI-Powered Decisions · Demo System — Capacity thresholds are configurable
      </footer>
    </BrowserRouter>
  )
}
