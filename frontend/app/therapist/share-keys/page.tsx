'use client'

import { useEffect, useState } from 'react'
import { Key, Calendar, User, CheckCircle, XCircle, Clock } from 'lucide-react'

interface ShareKey {
  id: string
  patient_id: string
  patient_name: string
  patient_email: string
  key_code: string
  status: 'active' | 'revoked' | 'expired'
  created_at: string
  expires_at: string | null
  last_accessed: string | null
  access_count: number
}

export default function ShareKeysPage() {
  const [shareKeys, setShareKeys] = useState<ShareKey[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'active' | 'revoked'>('all')

  useEffect(() => {
    fetchShareKeys()
  }, [])

  const fetchShareKeys = async () => {
    try {
      const response = await fetch('/api/v1/sharing/my-share-keys', {
        credentials: 'include'
      })

      if (response.ok) {
        const data = await response.json()
        setShareKeys(data.items || [])
      }
    } catch (error) {
      console.error('Failed to fetch share keys:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleRevokeKey = async (keyId: string) => {
    if (!confirm('Möchten Sie diesen Zugriff wirklich widerrufen?')) {
      return
    }

    try {
      const response = await fetch(`/api/v1/sharing/share-key/${keyId}/revoke`, {
        method: 'PUT',
        credentials: 'include'
      })

      if (response.ok) {
        fetchShareKeys() // Refresh list
      }
    } catch (error) {
      console.error('Failed to revoke share key:', error)
      alert('Fehler beim Widerrufen des Zugriffs')
    }
  }

  const filteredKeys = shareKeys.filter(key => {
    if (filter === 'all') return true
    return key.status === filter
  })

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle className="h-3 w-3 mr-1" />
            Aktiv
          </span>
        )
      case 'revoked':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
            <XCircle className="h-3 w-3 mr-1" />
            Widerrufen
          </span>
        )
      case 'expired':
        return (
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400">
            <Clock className="h-3 w-3 mr-1" />
            Abgelaufen
          </span>
        )
      default:
        return null
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Zugriffsverwaltung
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Verwalten Sie die ShareKeys und Zugriffe auf Patientendaten
          </p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex space-x-4 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => setFilter('all')}
          className={`pb-4 px-2 font-medium text-sm transition-colors ${
            filter === 'all'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          Alle ({shareKeys.length})
        </button>
        <button
          onClick={() => setFilter('active')}
          className={`pb-4 px-2 font-medium text-sm transition-colors ${
            filter === 'active'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          Aktiv ({shareKeys.filter(k => k.status === 'active').length})
        </button>
        <button
          onClick={() => setFilter('revoked')}
          className={`pb-4 px-2 font-medium text-sm transition-colors ${
            filter === 'revoked'
              ? 'border-b-2 border-primary text-primary'
              : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
          }`}
        >
          Widerrufen ({shareKeys.filter(k => k.status === 'revoked').length})
        </button>
      </div>

      {/* Share Keys List */}
      {filteredKeys.length > 0 ? (
        <div className="space-y-4">
          {filteredKeys.map((shareKey) => (
            <div
              key={shareKey.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow p-6"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4 flex-1">
                  <div className="bg-primary/10 p-3 rounded-full">
                    <Key className="h-6 w-6 text-primary" />
                  </div>

                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="font-semibold text-gray-900 dark:text-white">
                        {shareKey.patient_name}
                      </h3>
                      {getStatusBadge(shareKey.status)}
                    </div>

                    <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center">
                          <User className="h-4 w-4 mr-2" />
                          {shareKey.patient_email}
                        </div>
                        <div className="flex items-center">
                          <Key className="h-4 w-4 mr-2" />
                          {shareKey.key_code}
                        </div>
                      </div>

                      <div className="flex items-center space-x-4">
                        <div className="flex items-center">
                          <Calendar className="h-4 w-4 mr-2" />
                          Erstellt: {new Date(shareKey.created_at).toLocaleDateString('de-DE')}
                        </div>
                        {shareKey.expires_at && (
                          <div className="flex items-center">
                            <Clock className="h-4 w-4 mr-2" />
                            Läuft ab: {new Date(shareKey.expires_at).toLocaleDateString('de-DE')}
                          </div>
                        )}
                      </div>

                      <div className="flex items-center space-x-4">
                        <span>Zugriffsanzahl: {shareKey.access_count}</span>
                        {shareKey.last_accessed && (
                          <span>
                            Letzter Zugriff: {new Date(shareKey.last_accessed).toLocaleDateString('de-DE')}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                </div>

                {shareKey.status === 'active' && (
                  <button
                    onClick={() => handleRevokeKey(shareKey.id)}
                    className="ml-4 px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    Widerrufen
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-12 bg-white dark:bg-gray-800 rounded-lg shadow">
          <Key className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Keine ShareKeys gefunden
          </h3>
          <p className="text-gray-500 dark:text-gray-400">
            {filter === 'all'
              ? 'Es wurden noch keine ShareKeys erstellt'
              : `Keine ${filter === 'active' ? 'aktiven' : 'widerrufenen'} ShareKeys vorhanden`}
          </p>
        </div>
      )}
    </div>
  )
}
