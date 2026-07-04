import React, { useState, useEffect } from 'react'
import { api } from '../api.js'

export default function NodesList({ onNodesUpdate, onSelectNode }) {
  const [nodes, setNodes] = useState([])
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState({ name: '', address: '', type: 'vm' })
  const [loading, setLoading] = useState(false)

  useEffect(() => { loadNodes() }, [])

  const loadNodes = async () => {
    try {
      const data = await api.getNodes()
      const list = Array.isArray(data) ? data : []
      setNodes(list)
      
      if (typeof onNodesUpdate === 'function') {
        onNodesUpdate(list)
      }
    } catch (e) {
      console.error('Failed to load nodes:', e)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const newNode = await api.createNode(formData)
      setFormData({ name: '', address: '', type: 'vm' })
      setShowForm(false)

      await api.discoverHardware(newNode.id)
      
      await loadNodes()
      
      if (typeof onSelectNode === 'function' && newNode?.id) {
        onSelectNode(newNode.id)
      }
    } catch (e) {
      alert('Failed to create node')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async (id, name) => {
    if (!confirm(`Delete node "${name}"?`)) return
    try {
      await api.deleteNode(id)
      await loadNodes()
    } catch (e) {
      alert('Failed to delete node')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold">Nodes ({nodes.length})</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 rounded-lg font-medium"
        >
          {showForm ? '✕ Cancel' : '+ Add Node'}
        </button>
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="bg-gray-800 p-4 rounded-lg border border-gray-700 space-y-3">
          <div>
            <label className="block text-sm text-gray-400 mb-1">Name</label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2"
              placeholder="server-01"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Address</label>
            <input
              type="text"
              required
              value={formData.address}
              onChange={(e) => setFormData({...formData, address: e.target.value})}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2"
              placeholder="192.168.1.100"
            />
          </div>
          <div>
            <label className="block text-sm text-gray-400 mb-1">Type</label>
            <select
              value={formData.type}
              onChange={(e) => setFormData({...formData, type: e.target.value})}
              className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2"
            >
              <option value="vm">VM</option>
              <option value="physical">Physical</option>
              <option value="container">Container</option>
            </select>
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium disabled:opacity-50"
          >
            {loading ? 'Creating...' : 'Create Node'}
          </button>
        </form>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {nodes.map(node => (
          <div key={node.id} className="bg-gray-800 p-4 rounded-lg border border-gray-700">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="text-lg font-semibold">{node.name}</h3>
                <div className="text-sm text-gray-400 mt-1">{node.address}</div>
                <div className="flex gap-2 mt-2">
                  <span className="px-2 py-1 bg-blue-600 rounded text-xs">{node.type}</span>
                  <span className={`px-2 py-1 rounded text-xs ${
                    node.status === 'active' ? 'bg-green-600' : 'bg-red-600'
                  }`}>
                    {node.status}
                  </span>
                </div>
              </div>
              <button
                onClick={() => handleDelete(node.id, node.name)}
                className="text-red-400 hover:text-red-300 text-sm"
              >
                🗑️ Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {nodes.length === 0 && !showForm && (
        <div className="text-center py-12 text-gray-500">
          No nodes yet. Click "Add Node" to create one.
        </div>
      )}
    </div>
  )
}
