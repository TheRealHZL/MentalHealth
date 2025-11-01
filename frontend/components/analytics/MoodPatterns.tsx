'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { apiClient } from '@/lib/api'
import type { MoodPatterns as MoodPatternsType } from '@/types'

export function MoodPatterns() {
  const [patterns, setPatterns] = useState<MoodPatternsType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchPatterns()
  }, [])

  const fetchPatterns = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getMoodPatterns()
      setPatterns(data)
      setError(null)
    } catch (err) {
      setError('Fehler beim Laden der Stimmungsmuster')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getDayLabel = (day: string) => {
    const days: Record<string, string> = {
      'Monday': 'Montag',
      'Tuesday': 'Dienstag',
      'Wednesday': 'Mittwoch',
      'Thursday': 'Donnerstag',
      'Friday': 'Freitag',
      'Saturday': 'Samstag',
      'Sunday': 'Sonntag'
    }
    return days[day] || day
  }

  const getTimeLabel = (time: string) => {
    const times: Record<string, string> = {
      'morning': 'Morgens',
      'afternoon': 'Nachmittags',
      'evening': 'Abends',
      'night': 'Nachts'
    }
    return times[time] || time
  }

  const getMoodColor = (avgMood: number) => {
    if (avgMood >= 7) return 'bg-green-500'
    if (avgMood >= 5) return 'bg-yellow-500'
    return 'bg-red-500'
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Stimmungsmuster</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !patterns) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Stimmungsmuster</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error || 'Keine Daten verfügbar'}</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Stimmungsmuster</CardTitle>
        <CardDescription>Erkennen Sie Ihre Stimmungsmuster über die Woche</CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Best/Worst Day and Time */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-green-50 dark:bg-green-950 p-4 rounded-lg border border-green-200 dark:border-green-800">
            <p className="text-sm text-muted-foreground">Bester Tag</p>
            <p className="text-xl font-bold text-green-700 dark:text-green-400">
              {getDayLabel(patterns.bestDay)}
            </p>
          </div>
          <div className="bg-red-50 dark:bg-red-950 p-4 rounded-lg border border-red-200 dark:border-red-800">
            <p className="text-sm text-muted-foreground">Schlechtester Tag</p>
            <p className="text-xl font-bold text-red-700 dark:text-red-400">
              {getDayLabel(patterns.worstDay)}
            </p>
          </div>
          <div className="bg-blue-50 dark:bg-blue-950 p-4 rounded-lg border border-blue-200 dark:border-blue-800">
            <p className="text-sm text-muted-foreground">Beste Tageszeit</p>
            <p className="text-xl font-bold text-blue-700 dark:text-blue-400">
              {getTimeLabel(patterns.bestTime)}
            </p>
          </div>
        </div>

        {/* Weekly Heatmap */}
        <div>
          <h4 className="font-medium mb-3">Wochentage-Heatmap</h4>
          <div className="space-y-2">
            {patterns.patterns.map((pattern) => (
              <div key={pattern.day} className="flex items-center space-x-3">
                <div className="w-24 text-sm text-muted-foreground">
                  {getDayLabel(pattern.day)}
                </div>
                <div className="flex-1 h-8 bg-muted rounded-lg overflow-hidden relative">
                  <div
                    className={`h-full ${getMoodColor(pattern.avgMood)} transition-all`}
                    style={{ width: `${(pattern.avgMood / 10) * 100}%` }}
                  />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-medium text-white mix-blend-difference">
                      {pattern.avgMood.toFixed(1)} ({pattern.count} Einträge)
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center space-x-6 text-sm">
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-red-500 rounded"></div>
            <span className="text-muted-foreground">Niedrig (0-5)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-yellow-500 rounded"></div>
            <span className="text-muted-foreground">Mittel (5-7)</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-500 rounded"></div>
            <span className="text-muted-foreground">Hoch (7-10)</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
