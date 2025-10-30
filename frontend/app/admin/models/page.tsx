'use client'

import { useEffect, useState } from 'react'

interface ModelVersion {
  id: string
  model_name: string
  version: string
  is_active: boolean
  performance_metrics: {
    accuracy?: number
    loss?: number
    f1_score?: number
  }
  created_at: string
  created_by_id: string
}

export default function AdminModels() {
  const [models, setModels] = useState<ModelVersion[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedModel, setSelectedModel] = useState<ModelVersion | null>(null)

  useEffect(() => {
    fetchModels()
  }, [])

  const fetchModels = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/ai/training/models', {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setModels(data.items || [])
      }
    } catch (error) {
      console.error('Failed to fetch models:', error)
    } finally {
      setLoading(false)
    }
  }

  const activateModel = async (modelId: string) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/ai/training/models/${modelId}/activate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        fetchModels()
        alert('Model activated successfully!')
      } else {
        const error = await response.json()
        alert(`Failed to activate model: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to activate model:', error)
      alert('Failed to activate model')
    }
  }

  const evaluateModel = async (modelId: string) => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch(`/api/v1/ai/training/models/${modelId}/evaluate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setSelectedModel({ ...selectedModel!, performance_metrics: data.metrics })
        fetchModels()
        alert('Model evaluated successfully!')
      } else {
        const error = await response.json()
        alert(`Failed to evaluate model: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to evaluate model:', error)
      alert('Failed to evaluate model')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">AI Models</h2>
          <p className="text-gray-600 mt-2">Manage and evaluate trained AI models</p>
        </div>
        <button
          onClick={fetchModels}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
        >
          Refresh Models
        </button>
      </div>

      {/* Model Types Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <ModelTypeCard
          name="Emotion Classifier"
          count={models.filter(m => m.model_name === 'emotion_classifier').length}
          icon="😊"
        />
        <ModelTypeCard
          name="Mood Predictor"
          count={models.filter(m => m.model_name === 'mood_predictor').length}
          icon="🎭"
        />
        <ModelTypeCard
          name="Chat Generator"
          count={models.filter(m => m.model_name === 'chat_generator').length}
          icon="💬"
        />
        <ModelTypeCard
          name="Sentiment Analyzer"
          count={models.filter(m => m.model_name === 'sentiment_analyzer').length}
          icon="📊"
        />
      </div>

      {/* Models List */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">All Model Versions</h3>
        </div>

        {loading ? (
          <div className="text-center py-12 text-gray-500">
            Loading models...
          </div>
        ) : models.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No models found. Train a model to get started!
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Version
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Accuracy
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Loss
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {models.map((model) => (
                  <tr key={model.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">
                        {model.model_name}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{model.version}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        model.is_active
                          ? 'bg-green-100 text-green-800'
                          : 'bg-gray-100 text-gray-800'
                      }`}>
                        {model.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {model.performance_metrics?.accuracy
                        ? `${(model.performance_metrics.accuracy * 100).toFixed(2)}%`
                        : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {model.performance_metrics?.loss?.toFixed(4) || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(model.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                      {!model.is_active && (
                        <button
                          onClick={() => activateModel(model.id)}
                          className="text-blue-600 hover:text-blue-900 font-medium"
                        >
                          Activate
                        </button>
                      )}
                      <button
                        onClick={() => evaluateModel(model.id)}
                        className="text-purple-600 hover:text-purple-900 font-medium"
                      >
                        Evaluate
                      </button>
                      <button
                        onClick={() => setSelectedModel(model)}
                        className="text-gray-600 hover:text-gray-900 font-medium"
                      >
                        Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Model Details Modal */}
      {selectedModel && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full p-6">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-gray-900">Model Details</h3>
              <button
                onClick={() => setSelectedModel(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ✕
              </button>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-500">Model Name</label>
                  <p className="text-gray-900">{selectedModel.model_name}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Version</label>
                  <p className="text-gray-900">{selectedModel.version}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Status</label>
                  <p className="text-gray-900">{selectedModel.is_active ? 'Active' : 'Inactive'}</p>
                </div>
                <div>
                  <label className="text-sm font-medium text-gray-500">Created</label>
                  <p className="text-gray-900">{new Date(selectedModel.created_at).toLocaleString()}</p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-medium text-gray-500 mb-2">Performance Metrics</h4>
                <div className="bg-gray-50 rounded-lg p-4 space-y-2">
                  {selectedModel.performance_metrics?.accuracy && (
                    <div className="flex justify-between">
                      <span className="text-gray-700">Accuracy:</span>
                      <span className="font-medium text-gray-900">
                        {(selectedModel.performance_metrics.accuracy * 100).toFixed(2)}%
                      </span>
                    </div>
                  )}
                  {selectedModel.performance_metrics?.loss && (
                    <div className="flex justify-between">
                      <span className="text-gray-700">Loss:</span>
                      <span className="font-medium text-gray-900">
                        {selectedModel.performance_metrics.loss.toFixed(4)}
                      </span>
                    </div>
                  )}
                  {selectedModel.performance_metrics?.f1_score && (
                    <div className="flex justify-between">
                      <span className="text-gray-700">F1 Score:</span>
                      <span className="font-medium text-gray-900">
                        {selectedModel.performance_metrics.f1_score.toFixed(4)}
                      </span>
                    </div>
                  )}
                  {!selectedModel.performance_metrics?.accuracy &&
                   !selectedModel.performance_metrics?.loss &&
                   !selectedModel.performance_metrics?.f1_score && (
                    <p className="text-gray-500 text-sm">No metrics available yet. Run evaluation to generate metrics.</p>
                  )}
                </div>
              </div>
            </div>

            <div className="mt-6 flex justify-end space-x-3">
              <button
                onClick={() => setSelectedModel(null)}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300"
              >
                Close
              </button>
              {!selectedModel.is_active && (
                <button
                  onClick={() => {
                    activateModel(selectedModel.id)
                    setSelectedModel(null)
                  }}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  Activate Model
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function ModelTypeCard({ name, count, icon }: { name: string; count: number; icon: string }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center space-x-3">
        <div className="text-3xl">{icon}</div>
        <div>
          <p className="text-sm text-gray-600">{name}</p>
          <p className="text-2xl font-bold text-gray-900">{count}</p>
        </div>
      </div>
    </div>
  )
}
