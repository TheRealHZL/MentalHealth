'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Calendar, Clock, Target, TrendingUp } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import type { TherapySession } from '@/types'

interface SessionTrackerProps {
  sessions: TherapySession[]
}

export function SessionTracker({ sessions }: SessionTrackerProps) {
  const upcomingSession = sessions
    .filter(s => new Date(s.date) > new Date())
    .sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime())[0]

  const completedSessions = sessions.filter(s => new Date(s.date) <= new Date())
  const totalHours = completedSessions.reduce((sum, s) => sum + s.duration_minutes, 0) / 60

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Upcoming Session */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">Nächste Sitzung</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          {upcomingSession ? (
            <div>
              <div className="text-2xl font-bold">
                {formatDate(upcomingSession.date)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {upcomingSession.title}
              </p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Keine geplant</p>
          )}
        </CardContent>
      </Card>

      {/* Total Sessions */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">Gesamte Sitzungen</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{completedSessions.length}</div>
          <p className="text-xs text-muted-foreground mt-1">
            Abgeschlossene Sitzungen
          </p>
        </CardContent>
      </Card>

      {/* Total Hours */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">Gesamtdauer</CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{totalHours.toFixed(1)}h</div>
          <p className="text-xs text-muted-foreground mt-1">
            Therapiezeit insgesamt
          </p>
        </CardContent>
      </Card>

      {/* Progress */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-medium">Fortschritt</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">
            {completedSessions.length > 0 ? 'Gut' : '-'}
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {completedSessions.length > 0
              ? 'Regelmäßige Sitzungen'
              : 'Keine Daten'
            }
          </p>
        </CardContent>
      </Card>

      {/* Timeline */}
      {completedSessions.length > 0 && (
        <Card className="md:col-span-2 lg:col-span-4">
          <CardHeader>
            <CardTitle>Sitzungsverlauf</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {completedSessions
                .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime())
                .slice(0, 5)
                .map((session) => (
                  <div key={session.id} className="flex items-start gap-4 border-l-2 border-primary pl-4">
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium">{session.title}</h4>
                        <span className="text-sm text-muted-foreground">
                          {formatDate(session.date)}
                        </span>
                      </div>
                      {session.notes && (
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {session.notes}
                        </p>
                      )}
                      {session.goals && session.goals.length > 0 && (
                        <div className="flex flex-wrap gap-2 mt-2">
                          {session.goals.map((goal, idx) => (
                            <span
                              key={idx}
                              className="text-xs bg-primary/10 text-primary px-2 py-1 rounded"
                            >
                              {goal}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
