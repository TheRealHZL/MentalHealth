'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Activity, Heart, Moon, FileText, Calendar, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { formatDistanceToNow } from 'date-fns'
import { de } from 'date-fns/locale'

interface ActivityItem {
  id: string
  type: 'mood' | 'dream' | 'therapy_note' | 'therapy_session'
  title: string
  timestamp: string
  icon: React.ReactNode
  color: string
}

export function ActivityFeedWidget() {
  const [activities, setActivities] = useState<ActivityItem[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadRecentActivities()
  }, [])

  const loadRecentActivities = async () => {
    try {
      const activityList: ActivityItem[] = []

      // Fetch recent mood entries
      try {
        const moodResponse = await apiClient.getMoodEntries(1, 3)
        moodResponse.items.forEach((entry) => {
          activityList.push({
            id: `mood-${entry.id}`,
            type: 'mood',
            title: `Stimmung erfasst (${entry.mood_score}/10)`,
            timestamp: entry.created_at,
            icon: <Heart className="h-4 w-4" />,
            color: 'bg-red-500/10 text-red-600 dark:text-red-400',
          })
        })
      } catch (err) {
        console.error('Failed to load mood entries:', err)
      }

      // Fetch recent dream entries
      try {
        const dreamResponse = await apiClient.getDreamEntries(1, 3)
        dreamResponse.items.forEach((entry) => {
          activityList.push({
            id: `dream-${entry.id}`,
            type: 'dream',
            title: `Traum: ${entry.title}`,
            timestamp: entry.created_at,
            icon: <Moon className="h-4 w-4" />,
            color: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
          })
        })
      } catch (err) {
        console.error('Failed to load dream entries:', err)
      }

      // Fetch recent therapy notes
      try {
        const notesResponse = await apiClient.getTherapyNotes(1, 3)
        notesResponse.items.forEach((entry) => {
          activityList.push({
            id: `note-${entry.id}`,
            type: 'therapy_note',
            title: `Notiz: ${entry.title}`,
            timestamp: entry.created_at,
            icon: <FileText className="h-4 w-4" />,
            color: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
          })
        })
      } catch (err) {
        console.error('Failed to load therapy notes:', err)
      }

      // Fetch recent therapy sessions
      try {
        const sessionsResponse = await apiClient.getTherapySessions(1, 3)
        sessionsResponse.items.forEach((entry) => {
          activityList.push({
            id: `session-${entry.id}`,
            type: 'therapy_session',
            title: `Sitzung: ${entry.title}`,
            timestamp: entry.created_at,
            icon: <Calendar className="h-4 w-4" />,
            color: 'bg-green-500/10 text-green-600 dark:text-green-400',
          })
        })
      } catch (err) {
        console.error('Failed to load therapy sessions:', err)
      }

      // Sort by timestamp (most recent first)
      activityList.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())

      // Take top 8 activities
      setActivities(activityList.slice(0, 8))
    } catch (err) {
      console.error('Failed to load activities:', err)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Kürzliche Aktivitäten
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
          <Activity className="h-5 w-5" />
          Kürzliche Aktivitäten
        </CardTitle>
      </CardHeader>
      <CardContent>
        {activities.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">Noch keine Aktivitäten</p>
            <p className="text-xs mt-2">
              Ihre Aktivitäten werden hier angezeigt
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg border border-border hover:bg-muted/50 transition-colors"
              >
                <div className={`p-2 rounded-lg ${activity.color} flex-shrink-0`}>
                  {activity.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{activity.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    {formatDistanceToNow(new Date(activity.timestamp), {
                      addSuffix: true,
                      locale: de,
                    })}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
