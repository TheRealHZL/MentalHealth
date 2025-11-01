'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { WellnessScore } from '@/types'

export function WellnessScoreWidget() {
  const [wellnessData, setWellnessData] = useState<WellnessScore | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchWellnessScore()
  }, [])

  const fetchWellnessScore = async () => {
    try {
      setLoading(true)
      const data = await apiClient.getWellnessScore()
      setWellnessData(data)
      setError(null)
    } catch (err) {
      setError('Fehler beim Laden des Wellness Scores')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 75) return 'text-green-600 dark:text-green-400'
    if (score >= 50) return 'text-yellow-600 dark:text-yellow-400'
    return 'text-red-600 dark:text-red-400'
  }

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'improving':
        return <TrendingUp className="h-5 w-5 text-green-600 dark:text-green-400" />
      case 'declining':
        return <TrendingDown className="h-5 w-5 text-red-600 dark:text-red-400" />
      default:
        return <Minus className="h-5 w-5 text-gray-600 dark:text-gray-400" />
    }
  }

  const getTrendLabel = (trend: string) => {
    switch (trend) {
      case 'improving':
        return 'Verbessernd'
      case 'declining':
        return 'Abnehmend'
      default:
        return 'Stabil'
    }
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Wellness Score</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !wellnessData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Wellness Score</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error || 'Keine Daten verfügbar'}</p>
        </CardContent>
      </Card>
    )
  }

  const percentage = (wellnessData.score / 100) * 360

  return (
    <Card>
      <CardHeader>
        <CardTitle>Wellness Score</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center space-y-6">
          {/* Circular Progress */}
          <div className="relative w-40 h-40">
            <svg className="transform -rotate-90 w-40 h-40">
              {/* Background circle */}
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke="currentColor"
                strokeWidth="12"
                fill="transparent"
                className="text-muted"
              />
              {/* Progress circle */}
              <circle
                cx="80"
                cy="80"
                r="70"
                stroke="currentColor"
                strokeWidth="12"
                fill="transparent"
                strokeDasharray={`${2 * Math.PI * 70}`}
                strokeDashoffset={`${2 * Math.PI * 70 * (1 - wellnessData.score / 100)}`}
                className={getScoreColor(wellnessData.score)}
                strokeLinecap="round"
              />
            </svg>
            {/* Score in center */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className={`text-4xl font-bold ${getScoreColor(wellnessData.score)}`}>
                  {wellnessData.score}
                </div>
                <div className="text-sm text-muted-foreground">von 100</div>
              </div>
            </div>
          </div>

          {/* Trend Indicator */}
          <div className="flex items-center space-x-2">
            {getTrendIcon(wellnessData.trend)}
            <span className="text-sm font-medium">{getTrendLabel(wellnessData.trend)}</span>
          </div>

          {/* Factors */}
          <div className="w-full space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Stimmung</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${wellnessData.factors.mood * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium w-12 text-right">
                  {Math.round(wellnessData.factors.mood * 100)}%
                </span>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Energie</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${wellnessData.factors.energy * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium w-12 text-right">
                  {Math.round(wellnessData.factors.energy * 100)}%
                </span>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Schlaf</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-primary rounded-full"
                    style={{ width: `${wellnessData.factors.sleep * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium w-12 text-right">
                  {Math.round(wellnessData.factors.sleep * 100)}%
                </span>
              </div>
            </div>

            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Stress</span>
              <div className="flex items-center space-x-2">
                <div className="w-24 h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className="h-full bg-destructive rounded-full"
                    style={{ width: `${wellnessData.factors.stress * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium w-12 text-right">
                  {Math.round(wellnessData.factors.stress * 100)}%
                </span>
              </div>
            </div>
          </div>

          <p className="text-xs text-muted-foreground text-center">
            Aktualisiert: {new Date().toLocaleDateString('de-DE')}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
