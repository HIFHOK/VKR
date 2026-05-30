import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api.js'

export default function Dashboard({ selectedNode, onNodeSelect }) {
  const [resources, setResources] = useState([])
  const [metricsData, setMetricsData] = useState({})
  const [loading, setLoading] = useState(false)

  // Загружаем ресурсы при изменении выбранного узла
  useEffect(() => {
    if (selectedNode) loadResources(selectedNode)
  }, [selectedNode])

  // Авто-обновление метрик
  useEffect(() => {
    if (resources.length > 0) {
      loadAllMetrics()
      const interval = setInterval(loadAllMetrics, 30000)
      return () => clearInterval(interval)
    }
  }, [resources])

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
      {/* Кнопки управления */}
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

            {/* Карточки метрик (с гарантированным порядком: CPU → RAM → Disk → Network) */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {(() => {
          const typeOrder = { cpu: 1, memory: 2, disk: 3, network: 4 };
          const sortedResources = [...resources].sort((a, b) => 
            (typeOrder[a.type] || 99) - (typeOrder[b.type] || 99)
          );
          
          return sortedResources.map(resource => {
            const data = metricsData[resource.id];
            const stats = data?.stats;
            const currentValue = data?.history?.[0]?.value;
            
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
            );
          });
        })()}
      </div>

      {/* Графики */}
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

      {resources.length === 0 && selectedNode && (
        <div className="text-center py-12 text-gray-500">
          No resources configured for this node.
        </div>
      )}

      {!selectedNode && (
        <div className="text-center py-12 text-gray-500">
          <p className="mb-2">Select a node from the dropdown above</p>
        </div>
      )}
    </div>
  )
}