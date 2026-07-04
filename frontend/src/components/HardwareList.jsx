import React, { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { api } from '../api.js'

export default function HardwareList({ nodeId }) {
  useEffect(() => {
    console.log('[HW] nodeId =', nodeId, 'type:', typeof nodeId)
  }, [nodeId])

  const [components, setComponents] = useState([])
  const [selectedComponent, setSelectedComponent] = useState(null)
  const [metrics, setMetrics] = useState([])
  const [loading, setLoading] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [filter, setFilter] = useState('all')
  const [error, setError] = useState(null)

  useEffect(() => {
    if (nodeId) loadComponents()
  }, [nodeId, filter])

  useEffect(() => {
    if (selectedComponent) loadMetrics(selectedComponent)
  }, [selectedComponent])

  const loadComponents = async () => {
    console.log('[LOAD] >>> Start, nodeId =', nodeId, 'filter =', filter)
    
    if (!nodeId) {
      console.warn('[LOAD] nodeId missing, skipping')
      return
    }
    
    setLoading(true)
    setError(null)
    
    try {
      const data = await api.getHardware(nodeId, filter !== 'all' ? filter : null)
      console.log('[LOAD] API returned:', Array.isArray(data) ? `${data.length} items` : 'non-array', data)
      
      const componentsList = Array.isArray(data) ? data : []
      setComponents(componentsList)
      console.log('[LOAD] State updated with', componentsList.length, 'components')
    } catch (e) {
      console.error('[LOAD] ERROR:', e)
      setError('Failed to load: ' + e.message)
    } finally {
      setLoading(false)
      console.log('[LOAD] <<< Finished')
    }
  }

  const loadMetrics = async (compId) => {
    try {
      const data = await api.getComponentMetrics(compId, 50)
      const chartData = (Array.isArray(data) ? data : [])
        .map(m => ({
          time: new Date(m.timestamp).toLocaleTimeString(),
          value: m.value,
          id: m.id
        }))
        .reverse()
      setMetrics(chartData)
    } catch (e) {
      console.error('Failed to load metrics:', e)
      setMetrics([])
    }
  }

  const handleDiscover = async () => {
    console.log('[DISC] >>> Clicked, nodeId =', nodeId)
    
    if (!nodeId) {
      console.error('[DISC] ERROR: nodeId is falsy:', nodeId)
      alert('No node selected!')
      return
    }
    
    setLoading(true)
    console.log('[DISC] Calling api.discoverHardware(', nodeId, ')')
    
    try {
      const result = await api.discoverHardware(nodeId)
      console.log('[DISC] API result:', Array.isArray(result) ? `${result.length} components` : result)
      
      console.log('[DISC] Calling loadComponents()')
      await loadComponents()
      console.log('[DISC] loadComponents() finished')
      
      alert('✅ Discovery complete! Found ' + (Array.isArray(result) ? result.length : 'unknown') + ' components')
    } catch (e) {
      console.error('[DISC] ERROR:', e)
      alert('❌ Error: ' + (e.message || JSON.stringify(e)))
    } finally {
      setLoading(false)
      console.log('[DISC] setLoading(false)')
    }
  }

  const handleExport = async () => {
    setExporting(true)
    try {
      await api.exportAggregatedData(nodeId, 24)
    } catch (e) {
      alert('Export failed: ' + e.message)
    } finally {
      setExporting(false)
    }
  }

  const getTypeIcon = (type) => {
    const icons = { cpu: '🖥️', ram: '🧠', disk: '💾', network: '🌐' }
    return icons[type] || '🔧'
  }

  const getStatusColor = (val) => {
    const num = Number(val) || 0
    if (num >= 90) return 'text-red-500'
    if (num >= 70) return 'text-yellow-500'
    return 'text-green-500'
  }

  const getBarColor = (val) => {
    const num = Number(val) || 0
    if (num >= 90) return 'bg-red-500'
    if (num >= 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  if (!nodeId) return <div className="p-4 text-gray-400">Select a node first.</div>
  if (error) return <div className="p-4 text-red-400 bg-red-900/20 rounded">{error}</div>

  const componentsArray = Array.isArray(components) ? components : []
  const filtered = filter === 'all' 
    ? componentsArray 
    : componentsArray.filter(c => c?.component_type === filter)

  console.log('[RENDER] filtered.length =', filtered?.length, 'loading =', loading)

  return (
    <div className="space-y-6">
      {/* Заголовок */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Hardware Inventory</h2>
          <p className="text-gray-400 text-sm">Physical resources monitoring</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <select 
            value={filter} 
            onChange={(e) => setFilter(e.target.value)}
            className="bg-gray-800 border border-gray-700 text-white rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="all">All</option>
            <option value="cpu">CPU</option>
            <option value="ram">RAM</option>
            <option value="disk">Disk</option>
            <option value="network">Network</option>
          </select>
          <button
            onClick={handleDiscover}
            disabled={loading}
            className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded font-medium flex items-center gap-2"
          >
            {loading ? '⏳' : '🔍'} {loading ? 'Scanning...' : 'Discover'}
          </button>
          <button
            onClick={handleExport}
            disabled={exporting || !nodeId}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white rounded font-medium flex items-center gap-2"
          >
            {exporting ? '⏳' : '📥'} {exporting ? 'Exporting...' : 'Export CSV'}
          </button>
        </div>
      </div>

      {/* Карточки */}
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {filtered && filtered.length > 0 ? (
          filtered.map((comp, idx) => {
            try {
              const usage = Number(comp?.current_usage) || 0
              const isPercent = comp?.metric_query && (comp.metric_query.includes('* 100') || comp.metric_query.includes('100 -'))
              const displayVal = comp?.current_usage != null
                ? (isPercent ? `${usage.toFixed(1)}%` : `${usage.toFixed(2)} ${comp.current_usage_unit || ''}`)
                : 'N/A'
              
              const usagePercent = isPercent ? Math.min(usage, 100) : 0
              const barColor = getBarColor(usagePercent)
              const statusColor = getStatusColor(usagePercent)
              const isSelected = selectedComponent === comp?.id

              console.log(`[RENDER] Card #${idx}:`, comp?.name, 'usage:', usage)

              return (
                <div 
                  key={comp?.id || idx}
                  onClick={() => comp?.id && setSelectedComponent(comp.id)}
                  className={`bg-gray-800 border rounded-lg p-4 cursor-pointer transition-all hover:shadow-lg
                    ${isSelected ? 'border-blue-500 ring-2 ring-blue-500/50' : 'border-gray-700 hover:border-gray-600'}
                  `}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <span className="text-3xl">{getTypeIcon(comp?.component_type)}</span>
                      <div>
                        <h3 className="font-semibold text-white leading-tight">{comp?.name || 'Unknown'}</h3>
                        <p className="text-xs text-gray-500 font-mono">{comp?.component_id || ''}</p>
                      </div>
                    </div>
                    <span className={`text-sm font-bold ${statusColor}`}>{displayVal}</span>
                  </div>

                  <div className="space-y-2 mb-3">
                    <div className="flex justify-between text-xs text-gray-400">
                      <span>Capacity:</span>
                      <span className="text-white font-medium">
                        {comp?.max_capacity ? `${comp.max_capacity} ${comp.max_capacity_unit}` : 'Unknown'}
                      </span>
                    </div>
                    <div className="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
                      <div 
                        className={`h-full rounded-full transition-all duration-500 ${barColor}`}
                        style={{ width: `${usagePercent}%` }}
                      />
                    </div>
                  </div>

                  <div className="text-xs text-gray-500 flex justify-between">
                    <span>
                      Updated: {
                        comp?.updated_at || comp?.discovered_at 
                          ? new Date(comp.updated_at || comp.discovered_at).toLocaleTimeString() 
                          : 'N/A'
                      }
                    </span>
                    <span className="text-blue-400 hover:underline">View Graph →</span>
                  </div>
                </div>
              )
            } catch (err) {
              console.error(`[RENDER ERROR] Card #${idx}:`, err, comp)
              return null
            }
          })
        ) : (
          /* Пустота */
          <div className="col-span-full text-center py-12 text-gray-500 border border-dashed border-gray-700 rounded-lg">
            <p className="mb-2">
              {loading ? 'Loading components...' : 'No components found'}
            </p>
            {!loading && (
              <button onClick={handleDiscover} className="text-blue-400 hover:underline">
                Run Discovery
              </button>
            )}
          </div>
        )}
      </div>

      {/* Графики */}
      {selectedComponent && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-white">
              Metrics: {componentsArray.find(c => c?.id === selectedComponent)?.name || 'Unknown'}
            </h3>
            <button onClick={() => setSelectedComponent(null)} className="text-gray-400 hover:text-white">Close</button>
          </div>
          
          <div className="h-64 w-full">
            {metrics.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={metrics}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis dataKey="time" stroke="#9CA3AF" tick={{fontSize: 12}} minTickGap={20} />
                  <YAxis stroke="#9CA3AF" tick={{fontSize: 12}} />
                  <Tooltip contentStyle={{ backgroundColor: '#1F2937', border: '1px solid #374151' }} />
                  <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex items-center justify-center text-gray-500">
                <p>No history data yet. Wait for collector...</p>
              </div>
            )}
          </div>
          
          {metrics.length > 0 && (
            <div className="mt-4 flex gap-6 text-sm text-gray-400">
              <div><span className="text-white font-medium">Current:</span> {metrics[metrics.length - 1]?.value}</div>
              <div><span className="text-white font-medium">Min:</span> {Math.min(...metrics.map(m => m.value)).toFixed(2)}</div>
              <div><span className="text-white font-medium">Max:</span> {Math.max(...metrics.map(m => m.value)).toFixed(2)}</div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
