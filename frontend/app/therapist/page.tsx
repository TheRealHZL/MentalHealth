'use client'

import { useEffect, useState } from 'react'
import { Users, Key, Activity, TrendingUp } from 'lucide-react'
import Link from 'next/link'

interface DashboardStats {
  total_patients: number
  active_share_keys: number
  recent_patient_activity: any[]
  patients_needing_attention: any[]
}

export default function TherapistDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('/api/v1/users/dashboard', {
        credentials: 'include'
      })

      if (response.ok) {
        const data = await response.json()
        setStats(data)
      }
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Therapeuten-Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Willkommen zurück! Hier ist eine Übersicht Ihrer Patienten.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Gesamte Patienten
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                {stats?.total_patients || 0}
              </p>
            </div>
            <div className="bg-blue-100 dark:bg-blue-900/30 p-3 rounded-full">
              <Users className="h-6 w-6 text-blue-600 dark:text-blue-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Aktive Zugriffe
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                {stats?.active_share_keys || 0}
              </p>
            </div>
            <div className="bg-green-100 dark:bg-green-900/30 p-3 rounded-full">
              <Key className="h-6 w-6 text-green-600 dark:text-green-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Benötigen Aufmerksamkeit
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                {stats?.patients_needing_attention?.length || 0}
              </p>
            </div>
            <div className="bg-yellow-100 dark:bg-yellow-900/30 p-3 rounded-full">
              <Activity className="h-6 w-6 text-yellow-600 dark:text-yellow-400" />
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Aktive Einträge
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white mt-2">
                {stats?.recent_patient_activity?.length || 0}
              </p>
            </div>
            <div className="bg-purple-100 dark:bg-purple-900/30 p-3 rounded-full">
              <TrendingUp className="h-6 w-6 text-purple-600 dark:text-purple-400" />
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Neueste Aktivitäten
            </h2>
          </div>
          <div className="p-6">
            {stats?.recent_patient_activity && stats.recent_patient_activity.length > 0 ? (
              <div className="space-y-4">
                {stats.recent_patient_activity.slice(0, 5).map((activity: any, idx: number) => (
                  <div key={idx} className="flex items-center space-x-4">
                    <div className="flex-shrink-0 w-2 h-2 bg-blue-500 rounded-full"></div>
                    <div className="flex-1">
                      <p className="text-sm text-gray-900 dark:text-white">
                        {activity.message || 'Neue Aktivität'}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {activity.timestamp ? new Date(activity.timestamp).toLocaleString('de-DE') : 'Kürzlich'}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                Keine aktuellen Aktivitäten
              </p>
            )}
          </div>
        </div>

        {/* Patients Needing Attention */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Patienten mit Aufmerksamkeitsbedarf
            </h2>
          </div>
          <div className="p-6">
            {stats?.patients_needing_attention && stats.patients_needing_attention.length > 0 ? (
              <div className="space-y-4">
                {stats.patients_needing_attention.map((patient: any, idx: number) => (
                  <div key={idx} className="flex items-center justify-between p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        {patient.name || 'Patient'}
                      </p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">
                        {patient.reason || 'Benötigt Aufmerksamkeit'}
                      </p>
                    </div>
                    <Link
                      href={`/therapist/patients/${patient.id}`}
                      className="text-sm text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      Ansehen
                    </Link>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 dark:text-gray-400 text-center py-8">
                Alle Patienten sind versorgt ✓
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Action Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          href="/therapist/patients"
          className="block p-6 bg-blue-50 dark:bg-blue-900/20 border-2 border-blue-200 dark:border-blue-800 rounded-lg hover:shadow-lg transition-all"
        >
          <Users className="h-8 w-8 text-blue-600 dark:text-blue-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
            Patienten ansehen
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Übersicht aller betreuten Patienten
          </p>
        </Link>

        <Link
          href="/therapist/share-keys"
          className="block p-6 bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-800 rounded-lg hover:shadow-lg transition-all"
        >
          <Key className="h-8 w-8 text-green-600 dark:text-green-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
            Zugriffe verwalten
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            ShareKeys und Berechtigungen
          </p>
        </Link>

        <div className="block p-6 bg-purple-50 dark:bg-purple-900/20 border-2 border-purple-200 dark:border-purple-800 rounded-lg">
          <Activity className="h-8 w-8 text-purple-600 dark:text-purple-400 mb-3" />
          <h3 className="font-semibold text-gray-900 dark:text-white mb-1">
            Fortschritte analysieren
          </h3>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Kommende Funktion
          </p>
        </div>
      </div>
    </div>
  )
}
