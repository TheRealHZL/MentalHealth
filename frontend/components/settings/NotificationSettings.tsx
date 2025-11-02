'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Loader2, Check, AlertCircle, Bell, Mail, Calendar, Heart, TrendingUp } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { NotificationPreferences } from '@/types'

interface NotificationToggleProps {
  icon: React.ReactNode
  title: string
  description: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}

function NotificationToggle({ icon, title, description, checked, onChange, disabled }: NotificationToggleProps) {
  return (
    <div className="flex items-start gap-4 p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors">
      <div className="mt-1 text-muted-foreground">{icon}</div>
      <div className="flex-1 space-y-1">
        <div className="font-medium">{title}</div>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => onChange(!checked)}
        className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 ${
          checked ? 'bg-primary' : 'bg-input'
        }`}
      >
        <span
          className={`inline-block h-4 w-4 transform rounded-full bg-background transition-transform ${
            checked ? 'translate-x-6' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  )
}

export function NotificationSettings() {
  const [preferences, setPreferences] = useState<NotificationPreferences>({
    email_notifications: true,
    push_notifications: false,
    therapy_reminders: true,
    mood_tracking_reminders: true,
    weekly_insights: true,
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadPreferences()
  }, [])

  const loadPreferences = async () => {
    try {
      setIsLoading(true)
      const data = await apiClient.getNotificationPreferences()
      setPreferences(data)
    } catch (err) {
      console.error('Failed to load notification preferences:', err)
      // Use defaults on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      await apiClient.updateNotificationPreferences(preferences)
      setMessage({ type: 'success', text: 'Benachrichtigungseinstellungen gespeichert' })
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      console.error('Failed to save preferences:', err)
      setMessage({ type: 'error', text: 'Fehler beim Speichern der Einstellungen' })
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="py-12 flex justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Benachrichtigungen</CardTitle>
        <CardDescription>
          Verwalten Sie Ihre Benachrichtigungseinstellungen
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-3">
          <NotificationToggle
            icon={<Mail className="h-5 w-5" />}
            title="E-Mail-Benachrichtigungen"
            description="Erhalten Sie wichtige Updates per E-Mail"
            checked={preferences.email_notifications}
            onChange={(checked) =>
              setPreferences({ ...preferences, email_notifications: checked })
            }
          />

          <NotificationToggle
            icon={<Bell className="h-5 w-5" />}
            title="Push-Benachrichtigungen"
            description="Erhalten Sie Push-Benachrichtigungen auf Ihrem Gerät"
            checked={preferences.push_notifications}
            onChange={(checked) =>
              setPreferences({ ...preferences, push_notifications: checked })
            }
          />

          <NotificationToggle
            icon={<Calendar className="h-5 w-5" />}
            title="Therapie-Erinnerungen"
            description="Erinnerungen an anstehende Therapiesitzungen"
            checked={preferences.therapy_reminders}
            onChange={(checked) =>
              setPreferences({ ...preferences, therapy_reminders: checked })
            }
          />

          <NotificationToggle
            icon={<Heart className="h-5 w-5" />}
            title="Stimmungstracking-Erinnerungen"
            description="Tägliche Erinnerungen zum Erfassen Ihrer Stimmung"
            checked={preferences.mood_tracking_reminders}
            onChange={(checked) =>
              setPreferences({ ...preferences, mood_tracking_reminders: checked })
            }
          />

          <NotificationToggle
            icon={<TrendingUp className="h-5 w-5" />}
            title="Wöchentliche Insights"
            description="Erhalten Sie wöchentliche Zusammenfassungen und Erkenntnisse"
            checked={preferences.weekly_insights}
            onChange={(checked) =>
              setPreferences({ ...preferences, weekly_insights: checked })
            }
          />
        </div>

        {/* Message */}
        {message && (
          <div
            className={`flex items-center gap-2 p-3 rounded-md ${
              message.type === 'success'
                ? 'bg-green-50 dark:bg-green-950 text-green-900 dark:text-green-100'
                : 'bg-red-50 dark:bg-red-950 text-red-900 dark:text-red-100'
            }`}
          >
            {message.type === 'success' ? (
              <Check className="h-4 w-4" />
            ) : (
              <AlertCircle className="h-4 w-4" />
            )}
            <span className="text-sm">{message.text}</span>
          </div>
        )}

        {/* Save Button */}
        <Button onClick={handleSave} disabled={isSaving} className="w-full md:w-auto">
          {isSaving ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Wird gespeichert...
            </>
          ) : (
            'Änderungen speichern'
          )}
        </Button>
      </CardContent>
    </Card>
  )
}
