'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { TrendingUp, TrendingDown } from 'lucide-react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { apiClient } from '@/lib/api'
import type { ActivityCorrelation } from '@/types'

export function ActivityCorrelations() {
  const [correlations, setCorrelations] = useState<ActivityCorrelation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchCorrelations()
  }, [])

  const fetchCorrelations = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getMoodCorrelations()
      setCorrelations(data.sort((a, b) => Math.abs(b.impact) - Math.abs(a.impact)))
      setError(null)
    } catch (err) {
      setError('Fehler beim Laden der Aktivitätskorrelationen')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getImpactColor = (impact: number) => {
    if (impact > 0.5) return '#10b981' // green
    if (impact > 0) return '#3b82f6' // blue
    if (impact > -0.5) return '#f59e0b' // yellow
    return '#ef4444' // red
  }

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="font-medium">{data.activity}</p>
          <p className="text-sm text-muted-foreground">
            Impact: {data.impact > 0 ? '+' : ''}{data.impact.toFixed(2)}
          </p>
          <p className="text-sm text-muted-foreground">
            Häufigkeit: {data.count}x
          </p>
        </div>
      )
    }
    return null
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Aktivitäts-Korrelationen</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || correlations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Aktivitäts-Korrelationen</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error || 'Keine Daten verfügbar'}</p>
        </CardContent>
      </Card>
    )
  }

  const positiveCorrelations = correlations.filter(c => c.impact > 0)
  const negativeCorrelations = correlations.filter(c => c.impact < 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Aktivitäts-Korrelationen</CardTitle>
        <CardDescription>
          Wie beeinflussen Ihre Aktivitäten Ihre Stimmung?
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Chart */}
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={correlations} layout="horizontal" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
            <XAxis
              type="number"
              domain={[-1, 1]}
              stroke="hsl(var(--muted-foreground))"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <YAxis
              dataKey="activity"
              type="category"
              stroke="hsl(var(--muted-foreground))"
              tick={{ fill: 'hsl(var(--muted-foreground))' }}
            />
            <Tooltip content={<CustomTooltip />} />
            <Bar dataKey="impact" radius={[0, 8, 8, 0]}>
              {correlations.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getImpactColor(entry.impact)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Top Positive/Negative */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Positive Impact */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2 mb-3">
              <TrendingUp className="h-5 w-5 text-green-600" />
              <h4 className="font-medium">Positive Einflüsse</h4>
            </div>
            {positiveCorrelations.slice(0, 3).map((correlation) => (
              <div
                key={correlation.activity}
                className="bg-green-50 dark:bg-green-950 p-3 rounded-lg border border-green-200 dark:border-green-800"
              >
                <div className="flex justify-between items-center">
                  <span className="font-medium">{correlation.activity}</span>
                  <span className="text-green-700 dark:text-green-400 font-bold">
                    +{correlation.impact.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {correlation.count}x dokumentiert
                </p>
              </div>
            ))}
          </div>

          {/* Negative Impact */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2 mb-3">
              <TrendingDown className="h-5 w-5 text-red-600" />
              <h4 className="font-medium">Negative Einflüsse</h4>
            </div>
            {negativeCorrelations.slice(0, 3).map((correlation) => (
              <div
                key={correlation.activity}
                className="bg-red-50 dark:bg-red-950 p-3 rounded-lg border border-red-200 dark:border-red-800"
              >
                <div className="flex justify-between items-center">
                  <span className="font-medium">{correlation.activity}</span>
                  <span className="text-red-700 dark:text-red-400 font-bold">
                    {correlation.impact.toFixed(2)}
                  </span>
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {correlation.count}x dokumentiert
                </p>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
