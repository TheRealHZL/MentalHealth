'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { apiClient } from '@/lib/api'
import type { MoodTrend } from '@/types'
import { format } from 'date-fns'
import { de } from 'date-fns/locale'

type TimeRange = 7 | 30 | 90

export function MoodTrendsChart() {
  const [trends, setTrends] = useState<MoodTrend[]>([])
  const [timeRange, setTimeRange] = useState<TimeRange>(30)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchTrends()
  }, [timeRange])

  const fetchTrends = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getMoodTrends(timeRange)
      setTrends(data)
      setError(null)
    } catch (err) {
      setError('Fehler beim Laden der Stimmungstrends')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const formatXAxis = (dateStr: string) => {
    const date = new Date(dateStr)
    if (timeRange === 7) {
      return format(date, 'EEEEEE', { locale: de }) // Mo, Di, Mi...
    } else if (timeRange === 30) {
      return format(date, 'd. MMM', { locale: de }) // 1. Jan, 2. Jan...
    } else {
      return format(date, 'MMM', { locale: de }) // Jan, Feb...
    }
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium mb-2">
            {format(new Date(label), 'dd. MMMM yyyy', { locale: de })}
          </p>
          {payload.map((entry: any, index: number) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(1)}
            </p>
          ))}
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Stimmungstrends</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-80">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || trends.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Stimmungstrends</CardTitle>
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
        <div className="flex items-center justify-between">
          <CardTitle>Stimmungstrends</CardTitle>
          <div className="flex gap-2">
            <Button
              variant={timeRange === 7 ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeRange(7)}
            >
              7 Tage
            </Button>
            <Button
              variant={timeRange === 30 ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeRange(30)}
            >
              30 Tage
            </Button>
            <Button
              variant={timeRange === 90 ? 'default' : 'outline'}
              size="sm"
              onClick={() => setTimeRange(90)}
            >
              90 Tage
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={trends} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              dataKey="date"
              tickFormatter={formatXAxis}
              stroke="hsl(var(--muted-foreground))"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <YAxis
              domain={[0, 10]}
              stroke="hsl(var(--muted-foreground))"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
                color: 'hsl(var(--foreground))',
              }}
            />
            <Line
              type="monotone"
              dataKey="mood_score"
              name="Stimmung"
              stroke="hsl(var(--primary))"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="energy_level"
              name="Energie"
              stroke="hsl(142 76% 36%)"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="stress_level"
              name="Stress"
              stroke="hsl(0 84% 60%)"
              strokeWidth={2}
              dot={{ r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
