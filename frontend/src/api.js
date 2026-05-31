const API_BASE = '/api/v1'

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`)
    return res.json()
  },

  async getNodes() {
    const res = await fetch(`${API_BASE}/nodes`)
    return res.json()
  },

  async createNode(data) {
    const res = await fetch(`${API_BASE}/nodes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    return res.json()
  },

  async deleteNode(id) {
    await fetch(`${API_BASE}/nodes/${id}`, { method: 'DELETE' })
  },

  async getResources(nodeId) {
    const res = await fetch(`${API_BASE}/nodes/${nodeId}/resources`)
    return res.json()
  },

  async createResource(nodeId, data) {
    const res = await fetch(`${API_BASE}/nodes/${nodeId}/resources`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    })
    return res.json()
  },

  async getMetricHistory(resourceId, limit = 50) {
    const res = await fetch(`${API_BASE}/metrics/${resourceId}/history?limit=${limit}`)
    return res.json()
  },

  async getMetricStats(resourceId) {
    const res = await fetch(`${API_BASE}/metrics/${resourceId}/stats`)
    return res.json()
  },

  async collectMetrics() {
    const res = await fetch(`${API_BASE}/collect`, { method: 'POST' })
    return res.json()
  },

  async aggregateMetrics(period = 1) {
    const res = await fetch(`${API_BASE}/aggregation/aggregate?period=${period}`, {
      method: 'POST'
    })
    if (!res.ok) throw new Error('Failed to aggregate')
    return res.json()
  },

  async getHardware(nodeId, type = null) {
    const params = type ? `?component_type=${type}` : ''
    const res = await fetch(`${API_BASE}/hardware/nodes/${nodeId}/hardware${params}`)
    return res.json()
  },

  async discoverHardware(nodeId) {
    console.log('[API] >>> discoverHardware(', nodeId, ')');
    const url = `${API_BASE}/hardware/nodes/${nodeId}/hardware/discover`;
    console.log('[API] Fetch URL:', url);
    
    const res = await fetch(url, { method: 'POST' });
    console.log('[API] Response status:', res.status, 'ok:', res.ok);
    
    if (!res.ok) {
      const errText = await res.text().catch(() => 'unknown');
      console.error('[API] Error body:', errText);
      throw new Error(`Discovery failed: ${res.status} ${errText}`);
    }
    
    const data = await res.json();
    console.log('[API] <<< Parsed JSON, type:', typeof data, 'isArray:', Array.isArray(data));
    return data;
  },

  async getComponentMetrics(componentId, limit = 50) {
    const res = await fetch(`${API_BASE}/hardware/hardware/${componentId}/metrics?limit=${limit}`)
    return res.json()
  },

  async getHardwareSummary(nodeId) {
    const res = await fetch(`${API_BASE}/hardware/nodes/${nodeId}/hardware/summary`)
    return res.json()
  },

  async exportAggregatedData(nodeId, period = 24) {
    const url = `${API_BASE}/aggregation/nodes/${nodeId}/aggregated/export?period=${period}`
    console.log('Exporting from:', url)
  
    const res = await fetch(url)
    if (!res.ok) throw new Error(`Export failed: ${res.statusText}`)
  
    const blob = await res.blob()
    const downloadUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `aggregated_node_${nodeId}_period_${period}h.csv`
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(downloadUrl)
  }
}