'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Calendar, Loader2, Clock, ArrowRight } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { TherapySession } from '@/types'
import { format, formatDistanceToNow, isFuture, parseISO } from 'date-fns'
import { de } from 'date-fns/locale'
import Link from 'next/link'

export function UpcomingSessionsWidget() {
  const [upcomingSessions, setUpcomingSessions] = useState<TherapySession[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadUpcomingSessions()
  }, [])

  const loadUpcomingSessions = async () => {
    try {
      const response = await apiClient.getTherapySessions(1, 10)
      // Filter for future sessions and sort by date
      const future = response.items
        .filter((session) => {
          try {
            return isFuture(parseISO(session.date))
          } catch {
            return false
          }
        })
        .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())
        .slice(0, 3)

      setUpcomingSessions(future)
    } catch (err) {
      console.error('Failed to load upcoming sessions:', err)
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Anstehende Sitzungen
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
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            Anstehende Sitzungen
          </CardTitle>
          <Link
            href="/dashboard/therapy/sessions"
            className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
          >
            Alle
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        {upcomingSessions.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Calendar className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-sm">Keine anstehenden Sitzungen</p>
            <p className="text-xs mt-2">
              Zukünftige Therapiesitzungen werden hier angezeigt
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {upcomingSessions.map((session, index) => {
              const sessionDate = parseISO(session.date)
              const isNextSession = index === 0

              return (
                <div
                  key={session.id}
                  className={`p-4 rounded-lg border transition-all ${
                    isNextSession
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:bg-muted/50'
                  }`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 space-y-2">
                      <div className="flex items-center gap-2">
                        {isNextSession && (
                          <span className="text-xs px-2 py-0.5 rounded-full bg-primary text-primary-foreground font-medium">
                            Nächste
                          </span>
                        )}
                        <h4 className="font-medium text-sm">{session.title}</h4>
                      </div>

                      <div className="flex items-center gap-4 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          <span>
                            {format(sessionDate, 'dd.MM.yyyy', { locale: de })}
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          <span>{session.duration_minutes} Min.</span>
                        </div>
                      </div>

                      <p className="text-xs text-muted-foreground">
                        {formatDistanceToNow(sessionDate, {
                          addSuffix: true,
                          locale: de,
                        })}
                      </p>

                      {session.goals && session.goals.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {session.goals.slice(0, 2).map((goal, idx) => (
                            <span
                              key={idx}
                              className="text-xs px-2 py-0.5 rounded-full bg-muted"
                            >
                              {goal}
                            </span>
                          ))}
                          {session.goals.length > 2 && (
                            <span className="text-xs px-2 py-0.5 text-muted-foreground">
                              +{session.goals.length - 2}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
