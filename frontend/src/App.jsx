// src/App.jsx
import { Routes, Route, NavLink } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import ForecastView from './pages/ForecastView'
import ZoneAnalysis from './pages/ZoneAnalysis'
import Alerts from './pages/Alerts'
import { Zap } from 'lucide-react'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      {/* Navbar */}
      <nav className="sticky top-0 z-50 border-b border-white/[0.06] bg-grid-900/90 backdrop-blur-[20px]">
        <div className="max-w-screen-xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo */}
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/30
                            flex items-center justify-center">
              <Zap size={16} className="text-cyber-cyan" />
            </div>
            <div>
              <div className="text-white font-bold text-sm leading-none">Delhi Grid Intelligence</div>
              <div className="text-cyber-cyan text-[10px] font-medium tracking-widest uppercase opacity-70">
                AI Demand Forecasting Platform
              </div>
            </div>
          </div>

          {/* Live indicator */}
          <div className="hidden md:flex items-center gap-2 text-xs text-slate-400">
            <span className="pulse-dot" />
            <span>Live</span>
          </div>

          {/* Navigation */}
          <div className="flex items-center gap-1">
            {[
              { to: '/',          label: 'Dashboard' },
              { to: '/forecast',  label: 'Forecast'  },
              { to: '/zones',     label: 'Zones'     },
              { to: '/alerts',    label: 'Alerts'    },
            ].map(({ to, label }) => (
              <NavLink
                key={to}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `nav-link ${isActive ? 'active' : ''}`
                }
              >
                {label}
              </NavLink>
            ))}
          </div>
        </div>
      </nav>

      {/* Page content */}
      <main className="flex-1">
        <Routes>
          <Route path="/"          element={<Dashboard />} />
          <Route path="/forecast"  element={<ForecastView />} />
          <Route path="/zones"     element={<ZoneAnalysis />} />
          <Route path="/alerts"    element={<Alerts />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="border-t border-white/[0.04] py-4 text-center">
        <p className="text-xs text-slate-600 tracking-widest uppercase">
          AI-powered decisions · Human-controlled actions · Demo system — capacity thresholds are configurable
        </p>
      </footer>
    </div>
  )
}
