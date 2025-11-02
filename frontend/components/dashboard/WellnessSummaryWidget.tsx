'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { TrendingUp, TrendingDown, Minus, Loader2, Heart } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { WellnessScore } from '@/types'

export function WellnessSummaryWidget() {
  const [wellnessData, setWellnessData] = useState<WellnessScore | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    loadWellnessData()
  }, [])

  const loadWellnessData = async () => {
    try {
      const data = await apiClient.getWellnessScore()
      setWellnessData(data)
    } catch (err) {
      console.error('Failed to load wellness data:', err)
      // Use mock data
      setWellnessData({
        score: 75,
        trend: 'improving',
        factors: {
          mood: 78,
          energy: 72,
          sleep: 80,
          stress: 65,
        },
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getTrendIcon = (trend: 'improving' | 'stable' | 'declining') => {
    if (trend === 'improving') return <TrendingUp className="h-4 w-4 text-green-600 dark:text-green-400" />
    if (trend === 'declining') return <TrendingDown className="h-4 w-4 text-red-600 dark:text-red-400" />
    return <Minus className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
  }

  const getTrendText = (trend: 'improving' | 'stable' | 'declining') => {
    if (trend === 'improving') return 'Verbesserung'
    if (trend === 'declining') return 'Verschlechterung'
    return 'Stabil'
  }

  const getTrendColor = (trend: 'improving' | 'stable' | 'declining') => {
    if (trend === 'improving') return 'text-green-600 dark:text-green-400'
    if (trend === 'declining') return 'text-red-600 dark:text-red-400'
    return 'text-yellow-600 dark:text-yellow-400'
  }

  if (isLoading) {
    return (
      <Card className="h-full">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Heart className="h-5 w-5" />
            Wellness-Übersicht
          </CardTitle>
        </CardHeader>
        <CardContent className="flex justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  if (!wellnessData) return null

  const scoreColor =
    wellnessData.score >= 75
      ? 'text-green-600 dark:text-green-400'
      : wellnessData.score >= 50
      ? 'text-yellow-600 dark:text-yellow-400'
      : 'text-red-600 dark:text-red-400'

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Heart className="h-5 w-5" />
          Wellness-Übersicht
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Main Score */}
        <div className="text-center space-y-2">
          <div className={`text-5xl font-bold ${scoreColor}`}>{wellnessData.score}</div>
          <div className="flex items-center justify-center gap-2">
            {getTrendIcon(wellnessData.trend)}
            <span className={`text-sm font-medium ${getTrendColor(wellnessData.trend)}`}>
              {getTrendText(wellnessData.trend)}
            </span>
          </div>
        </div>

        {/* Factor Breakdown */}
        <div className="space-y-3">
          <div className="text-sm font-medium text-muted-foreground">Faktoren</div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Stimmung</span>
              <span className="font-medium">{wellnessData.factors.mood}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-blue-500 transition-all"
                style={{ width: `${wellnessData.factors.mood}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Energie</span>
              <span className="font-medium">{wellnessData.factors.energy}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${wellnessData.factors.energy}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Schlaf</span>
              <span className="font-medium">{wellnessData.factors.sleep}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-purple-500 transition-all"
                style={{ width: `${wellnessData.factors.sleep}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Stress (niedrig ist besser)</span>
              <span className="font-medium">{wellnessData.factors.stress}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-red-500 transition-all"
                style={{ width: `${wellnessData.factors.stress}%` }}
              />
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
