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

  async aggregateMetrics(hours = 1) {
    const res = await fetch(`${API_BASE}/metrics/aggregate?period_hours=${hours}`, { method: 'POST' })
    return res.json()
  }
}