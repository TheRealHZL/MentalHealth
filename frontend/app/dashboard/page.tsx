'use client'

import { useAuth } from '@/hooks/useAuth'
import { WellnessSummaryWidget } from '@/components/dashboard/WellnessSummaryWidget'
import { QuickActionsWidget } from '@/components/dashboard/QuickActionsWidget'
import { StreakTrackerWidget } from '@/components/dashboard/StreakTrackerWidget'
import { RecentMoodWidget } from '@/components/dashboard/RecentMoodWidget'
import { UpcomingSessionsWidget } from '@/components/dashboard/UpcomingSessionsWidget'
import { ActivityFeedWidget } from '@/components/dashboard/ActivityFeedWidget'
import { Sparkles } from 'lucide-react'

export default function DashboardPage() {
  const { user } = useAuth()

  const getGreeting = () => {
    const hour = new Date().getHours()
    if (hour < 12) return 'Guten Morgen'
    if (hour < 18) return 'Guten Tag'
    return 'Guten Abend'
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="relative overflow-hidden rounded-lg bg-gradient-to-br from-primary via-primary/90 to-primary/80 p-8 text-primary-foreground">
        <div className="relative z-10">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-6 w-6" />
            <h1 className="text-3xl font-bold">
              {getGreeting()}, {user?.first_name}!
            </h1>
          </div>
          <p className="text-primary-foreground/90">
            Willkommen zurück auf deinem Dashboard. Hier ist deine Übersicht für heute.
          </p>
        </div>
        {/* Decorative Background */}
        <div className="absolute top-0 right-0 opacity-10">
          <svg width="400" height="200" viewBox="0 0 400 200" fill="none">
            <circle cx="350" cy="50" r="100" fill="currentColor" />
            <circle cx="300" cy="150" r="80" fill="currentColor" />
          </svg>
        </div>
      </div>

      {/* Main Widget Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - 2/3 width on large screens */}
        <div className="lg:col-span-2 space-y-6">
          {/* Top Row - Quick Actions */}
          <QuickActionsWidget />

          {/* Second Row - Wellness & Streak */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <WellnessSummaryWidget />
            <StreakTrackerWidget />
          </div>

          {/* Third Row - Recent Mood */}
          <RecentMoodWidget />
        </div>

        {/* Right Column - 1/3 width on large screens */}
        <div className="space-y-6">
          {/* Upcoming Sessions */}
          <UpcomingSessionsWidget />

          {/* Activity Feed */}
          <ActivityFeedWidget />
        </div>
      </div>
    </div>
  )
}
