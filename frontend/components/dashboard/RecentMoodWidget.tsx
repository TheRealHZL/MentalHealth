'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Heart, Loader2, TrendingUp, TrendingDown, ArrowRight } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { MoodEntry } from '@/types'
import { format, formatDistanceToNow } from 'date-fns'
import { de } from 'date-fns/locale'
import Link from 'next/link'

export function RecentMoodWidget() {
  const [recentEntries, setRecentEntries] = useState<MoodEntry[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadRecentMoods()
  }, [])

  const loadRecentMoods = async () => {
    try {
      const response = await apiClient.getMoodEntries(1, 3)
      setRecentEntries(response.items)
    } catch (err) {
      console.error('Failed to load recent moods:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const getMoodEmoji = (score: number): string => {
    if (score >= 8) return '😄'
    if (score >= 6) return '🙂'
    if (score >= 4) return '😐'
    if (score >= 2) return '😕'
    return '😢'
  }

  const getMoodColor = (score: number): string => {
    if (score >= 7) return 'text-green-600 dark:text-green-400'
    if (score >= 5) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getTrend = (): { icon: React.ReactNode; text: string; color: string } | null => {
    if (recentEntries.length < 2) return null

    const latest = recentEntries[0].mood_score
    const previous = recentEntries[1].mood_score

    if (latest > previous) {
      return {
        icon: <TrendingUp className="h-4 w-4" />,
        text: 'Aufwärtstrend',
        color: 'text-green-600 dark:text-green-400',
      }
    } else if (latest < previous) {
      return {
        icon: <TrendingDown className="h-4 w-4" />,
        text: 'Abwärtstrend',
        color: 'text-red-600 dark:text-red-400',
      }
    }
    return null
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Heart className="h-5 w-5" />
            Aktuelle Stimmung
          </CardTitle>
        </CardHeader>
        <CardContent className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  const trend = getTrend()

  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Heart className="h-5 w-5" />
            Aktuelle Stimmung
          </CardTitle>
          <Link
            href="/dashboard/mood"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            Alle
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {recentEntries.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Heart className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">Noch keine Stimmungseinträge</p>
            <Link
              href="/dashboard/mood/new"
              className="text-sm text-primary hover:underline mt-2 inline-block"
            >
              Ersten Eintrag erstellen
            </Link>
          </div>
        ) : (
          <>
            {/* Latest Entry Highlight */}
            {recentEntries[0] && (
              <div className="p-4 rounded-lg bg-muted">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(recentEntries[0].created_at), {
                      addSuffix: true,
                      locale: de,
                    })}
                  </span>
                  {trend && (
                    <div className={`flex items-center gap-1 text-xs ${trend.color}`}>
                      {trend.icon}
                      <span>{trend.text}</span>
                    </div>
                  )}
                </div>
                <div className="flex items-center gap-4">
                  <div className="text-4xl">{getMoodEmoji(recentEntries[0].mood_score)}</div>
                  <div className="flex-1">
                    <div className={`text-2xl font-bold ${getMoodColor(recentEntries[0].mood_score)}`}>
                      {recentEntries[0].mood_score}/10
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Energie: {recentEntries[0].energy_level}/10 • Stress:{' '}
                      {recentEntries[0].stress_level}/10
                    </p>
                  </div>
                </div>
                {recentEntries[0].notes && (
                  <p className="text-sm text-muted-foreground mt-3 line-clamp-2">
                    {recentEntries[0].notes}
                  </p>
                )}
              </div>
            )}

            {/* Recent Entries List */}
            {recentEntries.length > 1 && (
              <div className="space-y-2">
                {recentEntries.slice(1).map((entry) => (
                  <div
                    key={entry.id}
                    className="flex items-center justify-between p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="text-2xl">{getMoodEmoji(entry.mood_score)}</div>
                      <div>
                        <div className={`text-sm font-medium ${getMoodColor(entry.mood_score)}`}>
                          {entry.mood_score}/10
                        </div>
                        <p className="text-xs text-muted-foreground">
                          {format(new Date(entry.created_at), 'dd.MM.yyyy HH:mm', { locale: de })}
                        </p>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {entry.activities.slice(0, 2).join(', ')}
                      {entry.activities.length > 2 && '...'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </CardContent>
    </Card>
  )
}
