'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, Shield, Calendar, User, Globe, Monitor, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { AccessLog } from '@/types'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

interface AccessLogViewerProps {
  shareKeyId?: string
}

export function AccessLogViewer({ shareKeyId }: AccessLogViewerProps) {
  const [accessLogs, setAccessLogs] = useState<AccessLog[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadAccessLogs()
  }, [shareKeyId])

  const loadAccessLogs = async () => {
    try {
      setIsLoading(true)
      setError(null)
      const response = await apiClient.getAccessLogs(shareKeyId, 1, 50)
      setAccessLogs(response.items)
    } catch (err) {
      console.error('Failed to load access logs:', err)
      setError('Fehler beim Laden der Zugriffsprotokolle')
    } finally {
      setIsLoading(false)
    }
  }

  const getDataTypeLabel = (dataType: string): string => {
    const labels: Record<string, string> = {
      mood: 'Stimmungsdaten',
      dreams: 'Traumtagebuch',
      therapy_notes: 'Therapienotizen',
      therapy_sessions: 'Therapiesitzungen',
      analytics: 'Analytik',
    }
    return labels[dataType] || dataType
  }

  const getDataTypeIcon = (dataType: string): string => {
    const icons: Record<string, string> = {
      mood: '😊',
      dreams: '🌙',
      therapy_notes: '📝',
      therapy_sessions: '🗓️',
      analytics: '📊',
    }
    return icons[dataType] || '📄'
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Shield className="h-5 w-5" />
          Zugriffsprotokolle
        </CardTitle>
        <CardDescription>
          Sehen Sie, wer auf Ihre geteilten Daten zugegriffen hat
        </CardDescription>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <div className="py-12 flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : error ? (
          <div className="flex items-center gap-2 p-3 rounded-md bg-red-50 dark:bg-red-950 text-red-900 dark:text-red-100">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        ) : accessLogs.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">
            <Shield className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Noch keine Zugriffe auf Ihre geteilten Daten</p>
            <p className="text-sm mt-2">
              Zugriffe werden hier angezeigt, sobald jemand Ihre Daten über einen Freigabeschlüssel aufruft
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {accessLogs.map((log) => (
              <div
                key={log.id}
                className="p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 space-y-2">
                    {/* Main Info */}
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{getDataTypeIcon(log.data_type)}</span>
                      <div>
                        <div className="font-medium">
                          {getDataTypeLabel(log.data_type)}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground mt-0.5">
                          <User className="h-3 w-3" />
                          <span>{log.accessed_by}</span>
                        </div>
                      </div>
                    </div>

                    {/* Details */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm text-muted-foreground">
                      <div className="flex items-center gap-2">
                        <Calendar className="h-4 w-4" />
                        <span>
                          {format(new Date(log.accessed_at), 'dd.MM.yyyy HH:mm', {
                            locale: de,
                          })}
                        </span>
                      </div>
                      {log.ip_address && (
                        <div className="flex items-center gap-2">
                          <Globe className="h-4 w-4" />
                          <span>{log.ip_address}</span>
                        </div>
                      )}
                      {log.user_agent && (
                        <div className="flex items-center gap-2">
                          <Monitor className="h-4 w-4" />
                          <span className="truncate" title={log.user_agent}>
                            {log.user_agent.length > 30
                              ? `${log.user_agent.substring(0, 30)}...`
                              : log.user_agent}
                          </span>
                        </div>
                      )}
                    </div>

                    {/* Share Key ID */}
                    <div className="text-xs text-muted-foreground">
                      Schlüssel-ID: <code className="bg-muted px-1 py-0.5 rounded">{log.share_key_id}</code>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
