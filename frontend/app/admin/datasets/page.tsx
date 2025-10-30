'use client'

import { useEffect, useState } from 'react'

interface Dataset {
  id: string
  name: string
  description: string
  dataset_type: string
  total_samples: number
  created_at: string
  is_active: boolean
}

export default function AdminDatasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [loading, setLoading] = useState(true)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [uploadFile, setUploadFile] = useState<File | null>(null)
  const [uploadMetadata, setUploadMetadata] = useState({
    name: '',
    description: '',
    dataset_type: 'conversation'
  })

  useEffect(() => {
    fetchDatasets()
  }, [])

  const fetchDatasets = async () => {
    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/ai/training/datasets', {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setDatasets(data.items || [])
      }
    } catch (error) {
      console.error('Failed to fetch datasets:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleFileUpload = async () => {
    if (!uploadFile || !uploadMetadata.name) {
      alert('Please provide file and name')
      return
    }

    const formData = new FormData()
    formData.append('file', uploadFile)
    formData.append('name', uploadMetadata.name)
    formData.append('description', uploadMetadata.description)
    formData.append('dataset_type', uploadMetadata.dataset_type)

    try {
      const token = localStorage.getItem('token')
      const response = await fetch('/api/v1/ai/training/datasets/upload', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData
      })

      if (response.ok) {
        setShowUploadModal(false)
        setUploadFile(null)
        setUploadMetadata({ name: '', description: '', dataset_type: 'conversation' })
        fetchDatasets()
        alert('Dataset uploaded successfully!')
      } else {
        const error = await response.json()
        alert(`Upload failed: ${error.detail}`)
      }
    } catch (error) {
      console.error('Upload failed:', error)
      alert('Upload failed')
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Training Datasets</h2>
          <p className="text-gray-600 mt-2">Manage training data for AI models</p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
        >
          📁 Upload Dataset
        </button>
      </div>

      {/* Datasets Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            Loading datasets...
          </div>
        ) : datasets.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500">
            No datasets found. Upload one to get started!
          </div>
        ) : (
          datasets.map((dataset) => (
            <DatasetCard key={dataset.id} dataset={dataset} />
          ))
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Upload Training Dataset</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dataset Name *
                </label>
                <input
                  type="text"
                  value={uploadMetadata.name}
                  onChange={(e) => setUploadMetadata({ ...uploadMetadata, name: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  placeholder="e.g., Mental Health Conversations 2024"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={uploadMetadata.description}
                  onChange={(e) => setUploadMetadata({ ...uploadMetadata, description: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  rows={3}
                  placeholder="Describe the dataset..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dataset Type
                </label>
                <select
                  value={uploadMetadata.dataset_type}
                  onChange={(e) => setUploadMetadata({ ...uploadMetadata, dataset_type: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="conversation">Conversation</option>
                  <option value="emotion">Emotion Labels</option>
                  <option value="sentiment">Sentiment</option>
                  <option value="mood">Mood Data</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  File (JSON or CSV) *
                </label>
                <input
                  type="file"
                  accept=".json,.csv"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                />
                {uploadFile && (
                  <p className="text-sm text-gray-600 mt-1">
                    Selected: {uploadFile.name} ({(uploadFile.size / 1024).toFixed(2)} KB)
                  </p>
                )}
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowUploadModal(false)}
                className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleFileUpload}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Upload
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function DatasetCard({ dataset }: { dataset: Dataset }) {
  return (
    <div className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <h3 className="font-semibold text-gray-900 text-lg">{dataset.name}</h3>
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
          dataset.is_active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
        }`}>
          {dataset.is_active ? 'Active' : 'Inactive'}
        </span>
      </div>

      <p className="text-sm text-gray-600 mb-4 line-clamp-2">{dataset.description}</p>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-gray-500">Type:</span>
          <span className="text-gray-900 font-medium">{dataset.dataset_type}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Samples:</span>
          <span className="text-gray-900 font-medium">{dataset.total_samples || 0}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-gray-500">Created:</span>
          <span className="text-gray-900 font-medium">
            {new Date(dataset.created_at).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  )
}
