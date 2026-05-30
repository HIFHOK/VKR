import React, { useState, useEffect } from 'react'
import { api } from './api.js'
import Dashboard from './components/Dashboard.jsx'
import NodesList from './components/NodesList.jsx'
import HardwareList from './components/HardwareList.jsx'

export default function App() {
  const [tab, setTab] = useState('dashboard')
  const [health, setHealth] = useState(null)
  
  // Глобальное состояние узла (общее для всех вкладок)
  const [selectedNode, setSelectedNode] = useState(null)
  const [nodes, setNodes] = useState([])

  // 🔥 ЗАГРУЖАЕМ УЗЛЫ ПРИ СТАРТЕ ПРИЛОЖЕНИЯ
  useEffect(() => {
    const loadNodes = async () => {
      try {
        const data = await api.getNodes()
        const nodesList = Array.isArray(data) ? data : []
        setNodes(nodesList)
        // Если есть узлы и ещё не выбран — выбираем первый
        if (nodesList.length > 0 && !selectedNode) {
          setSelectedNode(nodesList[0].id)
        }
      } catch (e) {
        console.error('Failed to load nodes:', e)
      }
    }
    loadNodes()
  }, [])  // ← Пустой массив зависимостей = выполнить только при монтировании

  // Проверка здоровья
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
      {/* Header */}
      <header className="bg-gray-800 shadow-lg border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-blue-400">⚙️ Accounting Subsystem</h1>
          <span className={`px-3 py-1 rounded-full text-sm ${
            health?.status === 'ok' ? 'bg-green-600' : 'bg-red-600'
          }`}>
            {health?.status === 'ok' ? '● Online' : '● Offline'}
          </span>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 flex gap-2 overflow-x-auto">
          <TabButton active={tab === 'dashboard'} onClick={() => setTab('dashboard')}>📊 Dashboard</TabButton>
          <TabButton active={tab === 'hardware'} onClick={() => setTab('hardware')}>🔧 Hardware</TabButton>
          <TabButton active={tab === 'nodes'} onClick={() => setTab('nodes')}>🖥️ Nodes</TabButton>
        </div>
      </nav>

      {/* 🔥 Глобальный селектор узлов — показываем если есть хотя бы 1 узел */}
      {nodes.length > 0 && (
        <div className="max-w-7xl mx-auto px-4 py-3 bg-gray-800/50 border-b border-gray-700 flex items-center gap-2 flex-wrap">
          <span className="text-sm text-gray-400">Active Node:</span>
          <select
            value={selectedNode || ''}
            onChange={(e) => setSelectedNode(parseInt(e.target.value))}
            className="bg-gray-800 border border-gray-700 rounded px-3 py-1 text-sm focus:ring-2 focus:ring-blue-500 outline-none min-w-[200px]"
          >
            <option value="" disabled>— Select a node —</option>
            {nodes.map(n => (
              <option key={n.id} value={n.id}>{n.name} ({n.address})</option>
            ))}
          </select>
          {selectedNode && (
            <span className="text-xs text-green-400 ml-2">● Active</span>
          )}
        </div>
      )}

      {/* Content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {tab === 'dashboard' && (
          <Dashboard 
            selectedNode={selectedNode}
            onNodeSelect={setSelectedNode}
          />
        )}
        {tab === 'hardware' && (
          <HardwareList nodeId={selectedNode} />
        )}
        {tab === 'nodes' && (
          <NodesList 
            onNodesUpdate={setNodes} 
            onSelectNode={setSelectedNode}
          />
        )}
        
        {/* Показать подсказку только если узлов вообще нет */}
        {nodes.length === 0 && tab !== 'nodes' && (
          <div className="text-center py-12 text-gray-500">
            <p className="mb-2">No nodes configured yet</p>
            <button onClick={() => setTab('nodes')} className="text-blue-400 hover:underline">
              Go to Nodes to add one →
            </button>
          </div>
        )}
      </main>
    </div>
  )
}

function TabButton({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-3 font-medium transition-colors whitespace-nowrap ${
        active 
          ? 'text-blue-400 border-b-2 border-blue-400' 
          : 'text-gray-400 hover:text-white'
      }`}
    >
      {children}
    </button>
  )
}