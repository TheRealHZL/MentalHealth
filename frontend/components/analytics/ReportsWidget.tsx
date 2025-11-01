'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { FileText, Download, Calendar } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { WeeklyInsight, MonthlyInsight } from '@/types'

type ReportType = 'weekly' | 'monthly'

export function ReportsWidget() {
  const [reportType, setReportType] = useState<ReportType>('weekly')
  const [weeklyReport, setWeeklyReport] = useState<WeeklyInsight | null>(null)
  const [monthlyReport, setMonthlyReport] = useState<MonthlyInsight | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchReports()
  }, [reportType])

  const fetchReports = async () => {
    try {
      setLoading(true)
      if (reportType === 'weekly') {
        const data = await apiClient.getWeeklyInsights()
        setWeeklyReport(data)
      } else {
        const data = await apiClient.getMonthlyInsights()
        setMonthlyReport(data)
      }
      setError(null)
    } catch (err) {
      setError('Fehler beim Laden der Berichte')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = () => {
    // Placeholder for PDF download functionality
    alert('PDF Download Feature kommt bald!')
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Berichte & Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || (reportType === 'weekly' && !weeklyReport) || (reportType === 'monthly' && !monthlyReport)) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Berichte & Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-destructive">{error || 'Keine Daten verfügbar'}</p>
        </CardContent>
      </Card>
    )
  }

  const currentReport = reportType === 'weekly' ? weeklyReport : monthlyReport

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Berichte & Insights</CardTitle>
            <CardDescription>Zusammenfassung Ihrer mentalen Gesundheit</CardDescription>
          </div>
          <div className="flex gap-2">
            <Button
              variant={reportType === 'weekly' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setReportType('weekly')}
            >
              Wöchentlich
            </Button>
            <Button
              variant={reportType === 'monthly' ? 'default' : 'outline'}
              size="sm"
              onClick={() => setReportType('monthly')}
            >
              Monatlich
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Report Header */}
        <div className="bg-primary/10 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Calendar className="h-5 w-5 text-primary" />
              <h3 className="font-semibold">
                {reportType === 'weekly'
                  ? `Woche: ${new Date(weeklyReport!.weekStart).toLocaleDateString('de-DE')} - ${new Date(weeklyReport!.weekEnd).toLocaleDateString('de-DE')}`
                  : `${monthlyReport!.month} ${monthlyReport!.year}`
                }
              </h3>
            </div>
            <Button variant="outline" size="sm" onClick={handleDownload}>
              <Download className="h-4 w-4 mr-2" />
              PDF
            </Button>
          </div>
          <div className="grid grid-cols-2 gap-4 mt-4">
            <div>
              <p className="text-sm text-muted-foreground">Durchschnittliche Stimmung</p>
              <p className="text-2xl font-bold">
                {currentReport?.avgMood.toFixed(1)}/10
              </p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Einträge</p>
              <p className="text-2xl font-bold">{currentReport?.totalEntries}</p>
            </div>
          </div>
        </div>

        {/* Insights */}
        <div>
          <div className="flex items-center space-x-2 mb-3">
            <FileText className="h-5 w-5 text-primary" />
            <h4 className="font-medium">Wichtige Erkenntnisse</h4>
          </div>
          <div className="space-y-2">
            {currentReport?.insights && currentReport.insights.length > 0 ? (
              currentReport.insights.map((insight, index) => (
                <div
                  key={index}
                  className="bg-muted p-3 rounded-lg border border-border"
                >
                  <p className="text-sm">{insight}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">
                Keine Erkenntnisse verfügbar. Tragen Sie mehr Stimmungen ein, um Insights zu erhalten.
              </p>
            )}
          </div>
        </div>

        {/* Recommendations */}
        <div>
          <h4 className="font-medium mb-3">Empfehlungen</h4>
          <div className="space-y-2">
            {currentReport?.recommendations && currentReport.recommendations.length > 0 ? (
              currentReport.recommendations.map((recommendation, index) => (
                <div
                  key={index}
                  className="bg-blue-50 dark:bg-blue-950 p-3 rounded-lg border border-blue-200 dark:border-blue-800"
                >
                  <p className="text-sm text-blue-900 dark:text-blue-100">{recommendation}</p>
                </div>
              ))
            ) : (
              <p className="text-sm text-muted-foreground">
                Keine Empfehlungen verfügbar.
              </p>
            )}
          </div>
        </div>

        {/* Progress Note */}
        <div className="bg-muted p-4 rounded-lg text-sm text-muted-foreground">
          <p>
            Ihre Fortschritte werden automatisch analysiert und wöchentlich/monatlich zusammengefasst.
            Tragen Sie regelmäßig Ihre Stimmung ein, um genauere Insights zu erhalten.
          </p>
        </div>
      </CardContent>
    </Card>
  )
}
