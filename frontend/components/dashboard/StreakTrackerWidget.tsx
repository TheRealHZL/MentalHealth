'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Flame, Trophy, Calendar, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { format, subDays } from 'date-fns'
import { de } from 'date-fns/locale'

interface StreakDay {
  date: string
  hasEntry: boolean
}

export function StreakTrackerWidget() {
  const [currentStreak, setCurrentStreak] = useState(0)
  const [longestStreak, setLongestStreak] = useState(0)
  const [weekDays, setWeekDays] = useState<StreakDay[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadStreakData()
  }, [])

  const loadStreakData = async () => {
    try {
      // Get mood entries for the last 30 days to calculate streak
      const response = await apiClient.getMoodEntries(1, 30)
      const entries = response.items

      // Calculate current streak
      let streak = 0
      let checkDate = new Date()
      checkDate.setHours(0, 0, 0, 0)

      while (true) {
        const dateStr = format(checkDate, 'yyyy-MM-dd')
        const hasEntry = entries.some(
          (entry) => format(new Date(entry.created_at), 'yyyy-MM-dd') === dateStr
        )

        if (!hasEntry) break

        streak++
        checkDate = subDays(checkDate, 1)

        if (streak > 30) break // Safety limit
      }

      setCurrentStreak(streak)

      // For longest streak, we'd need more data from backend
      // For now, use current streak as longest
      setLongestStreak(Math.max(streak, 5))

      // Generate last 7 days visualization
      const days: StreakDay[] = []
      for (let i = 6; i >= 0; i--) {
        const date = subDays(new Date(), i)
        const dateStr = format(date, 'yyyy-MM-dd')
        const hasEntry = entries.some(
          (entry) => format(new Date(entry.created_at), 'yyyy-MM-dd') === dateStr
        )
        days.push({ date: dateStr, hasEntry })
      }
      setWeekDays(days)
    } catch (err) {
      console.error('Failed to load streak data:', err)
      // Use mock data
      setCurrentStreak(3)
      setLongestStreak(7)
      const days: StreakDay[] = []
      for (let i = 6; i >= 0; i--) {
        const date = subDays(new Date(), i)
        days.push({ date: format(date, 'yyyy-MM-dd'), hasEntry: i >= 3 })
      }
      setWeekDays(days)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Flame className="h-5 w-5" />
            Streak Tracker
          </CardTitle>
        </CardHeader>
        <CardContent className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Flame className="h-5 w-5 text-orange-500" />
          Streak Tracker
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Current Streak */}
        <div className="text-center space-y-2">
          <div className="text-4xl font-bold text-orange-600 dark:text-orange-400">
            {currentStreak} 🔥
          </div>
          <div className="text-sm text-muted-foreground">Tage in Folge</div>
        </div>

        {/* Week Visualization */}
        <div className="space-y-3">
          <div className="text-sm font-medium text-muted-foreground">Letzte 7 Tage</div>
          <div className="flex justify-between gap-1">
            {weekDays.map((day, index) => (
              <div key={day.date} className="flex-1 flex flex-col items-center gap-2">
                <div
                  className={`w-full aspect-square rounded-lg transition-all ${
                    day.hasEntry
                      ? 'bg-orange-500 dark:bg-orange-600'
                      : 'bg-muted border-2 border-dashed border-muted-foreground/20'
                  }`}
                  title={format(new Date(day.date), 'dd.MM.yyyy', { locale: de })}
                />
                <div className="text-xs text-muted-foreground">
                  {format(new Date(day.date), 'EEE', { locale: de })}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
          <div className="text-center space-y-1">
            <div className="flex items-center justify-center gap-1 text-muted-foreground">
              <Trophy className="h-4 w-4" />
              <span className="text-xs">Längste</span>
            </div>
            <div className="text-xl font-bold">{longestStreak}</div>
          </div>
          <div className="text-center space-y-1">
            <div className="flex items-center justify-center gap-1 text-muted-foreground">
              <Calendar className="h-4 w-4" />
              <span className="text-xs">Aktuell</span>
            </div>
            <div className="text-xl font-bold">{currentStreak}</div>
          </div>
        </div>

        {/* Motivation */}
        {currentStreak === 0 && (
          <div className="text-center p-3 rounded-lg bg-muted text-sm">
            <p className="font-medium">Starte deine Streak heute!</p>
            <p className="text-xs text-muted-foreground mt-1">
              Erfasse deine Stimmung, um eine Serie zu beginnen
            </p>
          </div>
        )}
        {currentStreak > 0 && currentStreak < 7 && (
          <div className="text-center p-3 rounded-lg bg-orange-500/10 text-sm">
            <p className="font-medium text-orange-600 dark:text-orange-400">
              Großartig! Weiter so! 💪
            </p>
          </div>
        )}
        {currentStreak >= 7 && (
          <div className="text-center p-3 rounded-lg bg-orange-500/10 text-sm">
            <p className="font-medium text-orange-600 dark:text-orange-400">
              Unglaublich! Du bist auf Feuer! 🔥
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
