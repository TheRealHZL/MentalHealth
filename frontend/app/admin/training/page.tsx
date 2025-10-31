'use client'

import { useEffect, useState } from 'react'

interface TrainingJob {
  id: string
  model_type: string
  status: string
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  metrics?: {
    loss?: number
    accuracy?: number
    epoch?: number
    total_epochs?: number
  }
}

export default function AdminTraining() {
  const [trainingJobs, setTrainingJobs] = useState<TrainingJob[]>([])
  const [loading, setLoading] = useState(true)
  const [showStartModal, setShowStartModal] = useState(false)
  const [newTraining, setNewTraining] = useState({
    model_type: 'emotion_classifier',
    dataset_id: '',
    epochs: 50,
    batch_size: 32,
    learning_rate: 0.001
  })

  useEffect(() => {
    fetchTrainingJobs()
    const interval = setInterval(fetchTrainingJobs, 5000) // Refresh every 5s
    return () => clearInterval(interval)
  }, [])

  const fetchTrainingJobs = async () => {
    try {
      const response = await fetch('/api/v1/ai/training/jobs', {
        credentials: 'include' // Include cookies
      })

      if (response.ok) {
        const data = await response.json()
        setTrainingJobs(data.items || [])
      }
    } catch (error) {
      console.error('Failed to fetch training jobs:', error)
    } finally {
      setLoading(false)
    }
  }

  const startTraining = async () => {
    try {
      const response = await fetch('/api/v1/ai/training/start', {
        method: 'POST',
        credentials: 'include', // Include cookies
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(newTraining)
      })

      if (response.ok) {
        setShowStartModal(false)
        fetchTrainingJobs()
        alert('Training started successfully!')
      } else {
        const error = await response.json()
        alert(`Failed to start training: ${error.detail}`)
      }
    } catch (error) {
      console.error('Failed to start training:', error)
      alert('Failed to start training')
    }
  }

  const stopTraining = async (jobId: string) => {
    if (!confirm('Are you sure you want to stop this training job?')) return

    try {
      const response = await fetch(`/api/v1/ai/training/jobs/${jobId}/stop`, {
        method: 'POST',
        credentials: 'include' // Include cookies
      })

      if (response.ok) {
        fetchTrainingJobs()
        alert('Training stopped successfully!')
      }
    } catch (error) {
      console.error('Failed to stop training:', error)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">Model Training</h2>
          <p className="text-gray-600 mt-2">Train AI models globally for all users</p>
        </div>
        <button
          onClick={() => setShowStartModal(true)}
          className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 font-semibold"
        >
          🚀 Start New Training
        </button>
      </div>

      {/* Training Jobs List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Active Training Jobs</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {loading ? (
            <div className="p-8 text-center text-gray-500">Loading training jobs...</div>
          ) : trainingJobs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">No training jobs found</div>
          ) : (
            trainingJobs.map((job) => (
              <TrainingJobCard
                key={job.id}
                job={job}
                onStop={() => stopTraining(job.id)}
              />
            ))
          )}
        </div>
      </div>

      {/* Start Training Modal */}
      {showStartModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-md w-full p-6">
            <h3 className="text-xl font-bold text-gray-900 mb-4">Start New Training</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Model Type
                </label>
                <select
                  value={newTraining.model_type}
                  onChange={(e) => setNewTraining({ ...newTraining, model_type: e.target.value })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                >
                  <option value="emotion_classifier">Emotion Classifier</option>
                  <option value="mood_predictor">Mood Predictor</option>
                  <option value="chat_generator">Chat Generator</option>
                  <option value="sentiment_analyzer">Sentiment Analyzer</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Epochs
                </label>
                <input
                  type="number"
                  value={newTraining.epochs}
                  onChange={(e) => setNewTraining({ ...newTraining, epochs: parseInt(e.target.value) })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  min="1"
                  max="1000"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Batch Size
                </label>
                <input
                  type="number"
                  value={newTraining.batch_size}
                  onChange={(e) => setNewTraining({ ...newTraining, batch_size: parseInt(e.target.value) })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  min="1"
                  max="128"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Learning Rate
                </label>
                <input
                  type="number"
                  value={newTraining.learning_rate}
                  onChange={(e) => setNewTraining({ ...newTraining, learning_rate: parseFloat(e.target.value) })}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2"
                  step="0.0001"
                  min="0.0001"
                  max="0.1"
                />
              </div>
            </div>

            <div className="flex space-x-3 mt-6">
              <button
                onClick={() => setShowStartModal(false)}
                className="flex-1 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={startTraining}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700"
              >
                Start Training
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

function TrainingJobCard({ job, onStop }: { job: TrainingJob; onStop: () => void }) {
  const statusColors = {
    pending: 'bg-gray-100 text-gray-800',
    running: 'bg-blue-100 text-blue-800',
    completed: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
    stopped: 'bg-yellow-100 text-yellow-800',
  }[job.status] || 'bg-gray-100 text-gray-800'

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-3">
          <h4 className="font-semibold text-gray-900">{job.model_type.replace('_', ' ').toUpperCase()}</h4>
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors}`}>
            {job.status}
          </span>
        </div>
        {job.status === 'running' && (
          <button
            onClick={onStop}
            className="text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Stop
          </button>
        )}
      </div>

      {/* Progress Bar */}
      {job.status === 'running' && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>Progress</span>
            <span>{job.progress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${job.progress}%` }}
            ></div>
          </div>
        </div>
      )}

      {/* Metrics */}
      {job.metrics && (
        <div className="grid grid-cols-4 gap-4 mb-4">
          {job.metrics.epoch && (
            <div>
              <p className="text-xs text-gray-500">Epoch</p>
              <p className="text-sm font-semibold text-gray-900">
                {job.metrics.epoch}/{job.metrics.total_epochs}
              </p>
            </div>
          )}
          {job.metrics.loss !== undefined && (
            <div>
              <p className="text-xs text-gray-500">Loss</p>
              <p className="text-sm font-semibold text-gray-900">
                {job.metrics.loss.toFixed(4)}
              </p>
            </div>
          )}
          {job.metrics.accuracy !== undefined && (
            <div>
              <p className="text-xs text-gray-500">Accuracy</p>
              <p className="text-sm font-semibold text-gray-900">
                {(job.metrics.accuracy * 100).toFixed(2)}%
              </p>
            </div>
          )}
        </div>
      )}

      {/* Timestamps */}
      <div className="flex space-x-6 text-xs text-gray-500">
        <span>Created: {new Date(job.created_at).toLocaleString()}</span>
        {job.started_at && <span>Started: {new Date(job.started_at).toLocaleString()}</span>}
        {job.completed_at && <span>Completed: {new Date(job.completed_at).toLocaleString()}</span>}
      </div>
    </div>
  )
}
