'use client'

import { WellnessScoreWidget } from '@/components/analytics/WellnessScoreWidget'
import { MoodTrendsChart } from '@/components/analytics/MoodTrendsChart'
import { MoodPatterns } from '@/components/analytics/MoodPatterns'
import { ActivityCorrelations } from '@/components/analytics/ActivityCorrelations'
import { ReportsWidget } from '@/components/analytics/ReportsWidget'
import { BarChart3 } from 'lucide-react'

export default function AnalyticsPage() {
  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Page Header */}
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-primary/10 rounded-lg">
          <BarChart3 className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Verstehen Sie Ihre mentale Gesundheit durch datenbasierte Insights
          </p>
        </div>
      </div>

      {/* Grid Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Wellness Score - Takes 1 column */}
        <div className="lg:col-span-1">
          <WellnessScoreWidget />
        </div>

        {/* Mood Trends Chart - Takes 2 columns */}
        <div className="lg:col-span-2">
          <MoodTrendsChart />
        </div>
      </div>

      {/* Second Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Mood Patterns */}
        <MoodPatterns />

        {/* Activity Correlations */}
        <ActivityCorrelations />
      </div>

      {/* Third Row - Full Width */}
      <div className="grid grid-cols-1 gap-6">
        <ReportsWidget />
      </div>

      {/* Footer Info */}
      <div className="bg-muted p-6 rounded-lg text-center">
        <p className="text-sm text-muted-foreground">
          Alle Daten werden sicher verschlüsselt und sind nur für Sie sichtbar.
          Tragen Sie regelmäßig Ihre Stimmung ein, um genauere Analysen zu erhalten.
        </p>
      </div>
    </div>
  )
}
