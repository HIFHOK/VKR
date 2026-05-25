import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api.js'

export default function Dashboard() {
  const [nodes, setNodes] = useState([])
  const [selectedNode, setSelectedNode] = useState(null)
  const [resources, setResources] = useState([])
  const [metricsData, setMetricsData] = useState({})
  const [loading, setLoading] = useState(false)

  useEffect(() => { loadNodes() }, [])

  useEffect(() => {
    if (selectedNode) loadResources(selectedNode)
  }, [selectedNode])

  useEffect(() => {
    if (resources.length > 0) {
      loadAllMetrics()
      const interval = setInterval(loadAllMetrics, 30000)
      return () => clearInterval(interval)
    }
  }, [resources])

  const loadNodes = async () => {
    try {
      const data = await api.getNodes()
      const nodesList = Array.isArray(data) ? data : []
      setNodes(nodesList)
      if (nodesList.length > 0 && !selectedNode) {
        setSelectedNode(nodesList[0].id)
      }
    } catch (e) {
      console.error('Failed to load nodes:', e)
    }
  }

  const loadResources = async (nodeId) => {
    try {
      const data = await api.getResources(nodeId)
      setResources(Array.isArray(data) ? data : [])
    } catch (e) {
      console.error('Failed to load resources:', e)
      setResources([])
    }
  }

  const loadAllMetrics = async () => {
    const newData = {}
    for (const resource of resources) {
      try {
        const [history, stats] = await Promise.all([
          api.getMetricHistory(resource.id, 30),
          api.getMetricStats(resource.id)
        ])
        newData[resource.id] = { 
          history: Array.isArray(history) ? history : [], 
          stats 
        }
      } catch (e) {
        console.error(`Failed to load metrics for ${resource.id}:`, e)
      }
    }
    setMetricsData(newData)
  }

  const handleCollect = async () => {
    setLoading(true)
    try {
      await api.collectMetrics()
      await loadAllMetrics()
    } catch (e) {
      alert('Failed to collect metrics')
    }
    setLoading(false)
  }

  const handleAggregate = async () => {
    setLoading(true)
    try {
      await api.aggregateMetrics(1)
      alert('Aggregation completed!')
    } catch (e) {
      alert('Failed to aggregate')
    }
    setLoading(false)
  }

  return (
    <div className="space-y-6">
      <div className="flex gap-3">
        <button
          onClick={handleCollect}
          disabled={loading}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50"
        >
          {loading ? '⏳ Working...' : '🔄 Collect Metrics'}
        </button>
        <button
          onClick={handleAggregate}
          disabled={loading}
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg font-medium disabled:opacity-50"
        >
          📊 Aggregate (1h)
        </button>
      </div>

      {nodes.length > 1 && (
        <div>
          <label className="text-sm text-gray-400">Select Node:</label>
          <select
            value={selectedNode || ''}
            onChange={(e) => setSelectedNode(parseInt(e.target.value))}
            className="ml-2 bg-gray-800 border border-gray-700 rounded px-3 py-1"
          >
            {nodes.map(n => (
              <option key={n.id} value={n.id}>{n.name}</option>
            ))}
          </select>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {resources.map(resource => {
          const data = metricsData[resource.id]
          const stats = data?.stats
          const currentValue = data?.history?.[0]?.value
          
          return (
            <div key={resource.id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
              <div className="text-sm text-gray-400">{resource.name}</div>
              <div className="text-3xl font-bold mt-2">
                {currentValue !== undefined ? currentValue.toFixed(2) : '--'}{' '}
                <span className="text-lg text-gray-400">{resource.unit}</span>
              </div>
              {stats && (
                <div className="mt-3 text-xs text-gray-500 space-y-1">
                  <div>Min: {stats.min?.toFixed(2) || '-'} | Max: {stats.max?.toFixed(2) || '-'}</div>
                  <div>Avg: {stats.avg?.toFixed(2) || '-'} | Records: {stats.records}</div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {resources.map(resource => {
        const history = metricsData[resource.id]?.history || []
        const chartData = history
          .map(m => ({
            time: new Date(m.timestamp).toLocaleTimeString(),
            value: m.value
          }))
          .reverse()

        if (chartData.length === 0) return null

        return (
          <div key={resource.id} className="bg-gray-800 rounded-lg p-4 border border-gray-700">
            <h3 className="text-lg font-semibold mb-4">{resource.name} (Last 30 values)</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                <XAxis dataKey="time" stroke="#9CA3AF" />
                <YAxis stroke="#9CA3AF" />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }}
                />
                <Line 
                  type="monotone" 
                  dataKey="value" 
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )
      })}

      {resources.length === 0 && (
        <div className="text-center py-12 text-gray-500">
          No resources configured. Go to Nodes tab to add some.
        </div>
      )}
    </div>
  )
}