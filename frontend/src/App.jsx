import { NavLink, Route, Routes } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import DashboardPage from './pages/DashboardPage'
import SettingsPage from './pages/SettingsPage'

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <div className="mx-auto max-w-7xl p-4">
        <header className="mb-4 rounded-xl border border-slate-800 bg-slate-900/80 p-4 flex items-center justify-between">
          <h1 className="text-xl font-bold">Industrial RAG Studio</h1>
          <nav className="flex gap-3 text-sm">
            <NavLink className="px-3 py-1 rounded bg-slate-800" to="/">Chat</NavLink>
            <NavLink className="px-3 py-1 rounded bg-slate-800" to="/dashboard">Dashboard</NavLink>
            <NavLink className="px-3 py-1 rounded bg-slate-800" to="/settings">Settings</NavLink>
          </nav>
        </header>
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
    </div>
  )
}
