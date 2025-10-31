'use client'

import { useEffect, useState } from 'react'

interface Stats {
  totalUsers: number
  activeTrainingJobs: number
  totalModels: number
  totalDatasets: number
  systemHealth: string
}

interface RecentActivity {
  id: string
  type: string
  message: string
  timestamp: string
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [recentActivity, setRecentActivity] = useState<RecentActivity[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      // Fetch stats using apiClient (uses httpOnly cookies automatically)
      const statsData = await fetch('/api/v1/admin/stats', {
        credentials: 'include' // Include cookies
      })

      if (statsData.ok) {
        const data = await statsData.json()
        setStats(data)
      }

      // Fetch recent activity
      const activityRes = await fetch('/api/v1/admin/activity?limit=10', {
        credentials: 'include' // Include cookies
      })

      if (activityRes.ok) {
        const activityData = await activityRes.json()
        setRecentActivity(activityData.items || [])
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center py-12">Loading dashboard...</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold text-gray-900">Admin Dashboard</h2>
        <p className="text-gray-600 mt-2">Monitor system health and manage AI models</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Users"
          value={stats?.totalUsers || 0}
          icon="👥"
          color="blue"
        />
        <StatCard
          title="Active Training Jobs"
          value={stats?.activeTrainingJobs || 0}
          icon="🔄"
          color="yellow"
        />
        <StatCard
          title="AI Models"
          value={stats?.totalModels || 0}
          icon="🧠"
          color="purple"
        />
        <StatCard
          title="Datasets"
          value={stats?.totalDatasets || 0}
          icon="📊"
          color="green"
        />
      </div>

      {/* System Health */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">System Health</h3>
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${stats?.systemHealth === 'healthy' ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-gray-700 capitalize">{stats?.systemHealth || 'Unknown'}</span>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <QuickActionButton
            href="/admin/training"
            icon="🚀"
            title="Start Training"
            description="Train AI models with new data"
          />
          <QuickActionButton
            href="/admin/datasets"
            icon="📁"
            title="Upload Dataset"
            description="Add new training data"
          />
          <QuickActionButton
            href="/admin/models"
            icon="🔍"
            title="Evaluate Models"
            description="Check model performance"
          />
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
        {recentActivity.length === 0 ? (
          <p className="text-gray-500 text-sm">No recent activity</p>
        ) : (
          <div className="space-y-3">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm text-gray-900">{activity.message}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {new Date(activity.timestamp).toLocaleString()}
                  </p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  activity.type === 'training' ? 'bg-blue-100 text-blue-800' :
                  activity.type === 'model' ? 'bg-purple-100 text-purple-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {activity.type}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ title, value, icon, color }: { title: string; value: number; icon: string; color: string }) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
    green: 'bg-green-50 text-green-600',
  }[color]

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
        </div>
        <div className={`text-4xl ${colorClasses} p-3 rounded-lg`}>
          {icon}
        </div>
      </div>
    </div>
  )
}

function QuickActionButton({ href, icon, title, description }: { href: string; icon: string; title: string; description: string }) {
  return (
    <a
      href={href}
      className="block p-4 border-2 border-gray-200 rounded-lg hover:border-blue-500 hover:shadow-md transition-all"
    >
      <div className="text-3xl mb-2">{icon}</div>
      <h4 className="font-semibold text-gray-900">{title}</h4>
      <p className="text-sm text-gray-600 mt-1">{description}</p>
    </a>
  )
}
