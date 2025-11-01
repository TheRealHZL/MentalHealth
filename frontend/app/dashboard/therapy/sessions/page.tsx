'use client'

import { useEffect, useState } from 'react'
import { Button } from '@/components/ui/button'
import { SessionTracker } from '@/components/therapy/SessionTracker'
import { Calendar } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { TherapySession } from '@/types'

export default function TherapySessionsPage() {
  const [sessions, setSessions] = useState<TherapySession[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchSessions()
  }, [])

  const fetchSessions = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.getTherapySessions(1, 100)
      setSessions(response.items)
    } catch (err) {
      console.error('Failed to fetch sessions:', err)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <Calendar className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Therapiesitzungen</h1>
            <p className="text-muted-foreground">
              Übersicht Ihrer Sitzungen und Fortschritte
            </p>
          </div>
        </div>
      </div>

      {/* Session Tracker */}
      <SessionTracker sessions={sessions} />

      {/* Info */}
      {sessions.length === 0 && (
        <div className="text-center py-12 bg-muted/50 rounded-lg">
          <Calendar className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
          <p className="text-muted-foreground">
            Noch keine Sitzungen dokumentiert
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Erstellen Sie Therapienotizen, um Ihren Fortschritt zu verfolgen
          </p>
        </div>
      )}
    </div>
  )
}
