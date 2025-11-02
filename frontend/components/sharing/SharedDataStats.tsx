'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Key, Activity, CheckCircle, Share2, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { SharedDataStats } from '@/types'

export function SharedDataStatsComponent() {
  const [stats, setStats] = useState<SharedDataStats | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  useEffect(() => {
    loadStats()
  }, [])

  const loadStats = async () => {
    try {
      setIsLoading(true)
      const data = await apiClient.getSharedDataStats()
      setStats(data)
    } catch (err) {
      console.error('Failed to load stats:', err)
      // Use defaults
      setStats({
        total_share_keys: 0,
        active_share_keys: 0,
        total_accesses: 0,
        data_types_shared: [],
      })
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i}>
            <CardContent className="p-6 flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </CardContent>
          </Card>
        ))}
      </div>
    )
  }

  if (!stats) return null

  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Key className="h-4 w-4" />
            Gesamt Schlüssel
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_share_keys}</div>
          <p className="text-xs text-muted-foreground mt-1">Alle erstellten Schlüssel</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <CheckCircle className="h-4 w-4" />
            Aktive Schlüssel
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-green-600 dark:text-green-400">
            {stats.active_share_keys}
          </div>
          <p className="text-xs text-muted-foreground mt-1">Derzeit gültig</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Zugriffe
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_accesses}</div>
          <p className="text-xs text-muted-foreground mt-1">Gesamte Zugriffe</p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm font-medium text-muted-foreground flex items-center gap-2">
            <Share2 className="h-4 w-4" />
            Geteilte Datentypen
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.data_types_shared.length}</div>
          <p className="text-xs text-muted-foreground mt-1">Verschiedene Typen</p>
        </CardContent>
      </Card>
    </div>
  )
}
