import React, { useState, useEffect } from 'react'
import { api } from './api.js'
import Dashboard from './components/Dashboard.jsx'
import NodesList from './components/NodesList.jsx'

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [health, setHealth] = useState(null)

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await api.getHealth()
        setHealth(data)
      } catch (e) {
        setHealth({ status: 'error' })
      }
    }
    checkHealth()
    const interval = setInterval(checkHealth, 10000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      <header className="bg-gray-800 shadow-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-blue-400">🖥️ Accounting Subsystem</h1>
          <span className={`px-3 py-1 rounded-full text-sm ${
            health?.status === 'ok' ? 'bg-green-600' : 'bg-red-600'
          }`}>
            {health?.status === 'ok' ? '● Online' : '● Offline'}
          </span>
        </div>
      </header>

      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 flex gap-2">
          <TabButton active={tab === 'dashboard'} onClick={() => setTab('dashboard')}>
            📊 Dashboard
          </TabButton>
          <TabButton active={tab === 'nodes'} onClick={() => setTab('nodes')}>
            🖥️ Nodes
          </TabButton>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 py-6">
        {tab === 'dashboard' && <Dashboard />}
        {tab === 'nodes' && <NodesList />}
      </main>
    </div>
  )
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-3 font-medium transition-colors ${
        active 
          ? 'text-blue-400 border-b-2 border-blue-400' 
          : 'text-gray-400 hover:text-white'
      }`}
    >
      {children}
    </button>
  )
}