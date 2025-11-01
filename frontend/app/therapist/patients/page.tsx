'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { Users, Search, Calendar, Activity } from 'lucide-react'

interface Patient {
  id: string
  first_name: string
  last_name: string
  email: string
  share_key_created_at: string
  last_activity: string | null
  status: string
}

export default function PatientsPage() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')

  useEffect(() => {
    fetchPatients()
  }, [])

  const fetchPatients = async () => {
    try {
      const response = await fetch('/api/v1/sharing/my-patients', {
        credentials: 'include'
      })

      if (response.ok) {
        const data = await response.json()
        setPatients(data)
      }
    } catch (error) {
      console.error('Failed to fetch patients:', error)
    } finally {
      setLoading(false)
    }
  }

  const filteredPatients = patients.filter(patient =>
    `${patient.first_name} ${patient.last_name} ${patient.email}`
      .toLowerCase()
      .includes(searchTerm.toLowerCase())
  )

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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Meine Patienten
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            {patients.length} Patient{patients.length !== 1 ? 'en' : ''} insgesamt
          </p>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Patienten suchen..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-800 dark:text-white"
        />
      </div>

      {/* Patients List */}
      {filteredPatients.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredPatients.map((patient) => (
            <Link
              key={patient.id}
              href={`/therapist/patients/${patient.id}`}
              className="block bg-white dark:bg-gray-800 rounded-lg shadow hover:shadow-lg transition-shadow p-6"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="bg-primary/10 p-2 rounded-full">
                    <Users className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">
                      {patient.first_name} {patient.last_name}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {patient.email}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex items-center text-gray-600 dark:text-gray-400">
                  <Calendar className="h-4 w-4 mr-2" />
                  <span>
                    Zugriff seit:{' '}
                    {new Date(patient.share_key_created_at).toLocaleDateString('de-DE')}
                  </span>
                </div>

                {patient.last_activity && (
                  <div className="flex items-center text-gray-600 dark:text-gray-400">
                    <Activity className="h-4 w-4 mr-2" />
                    <span>
                      Letzte Aktivität:{' '}
                      {new Date(patient.last_activity).toLocaleDateString('de-DE')}
                    </span>
                  </div>
                )}

                <div className="mt-4">
                  <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                    patient.status === 'active'
                      ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                      : 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
                  }`}>
                    {patient.status === 'active' ? 'Aktiv' : 'Inaktiv'}
                  </span>
                </div>
              </div>
            </Link>
          ))}
        </div>
      ) : searchTerm ? (
        <div className="text-center py-12">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Keine Patienten gefunden
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            Versuchen Sie einen anderen Suchbegriff
          </p>
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow">
          <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Noch keine Patienten
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            Patienten können Ihnen über ShareKeys Zugriff auf ihre Daten gewähren
          </p>
          <Link
            href="/therapist/share-keys"
            className="inline-flex items-center px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors"
          >
            Zu den ShareKeys
          </Link>
        </div>
      )}
    </div>
  )
}
