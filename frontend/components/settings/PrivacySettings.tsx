'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import { Loader2, Check, AlertCircle, Eye, Share2, Download, Shield } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { PrivacySettings as PrivacySettingsType } from '@/types'

interface PrivacyToggleProps {
  icon: React.ReactNode
  title: string
  description: string
  checked: boolean
  onChange: (checked: boolean) => void
  disabled?: boolean
}

function PrivacyToggle({ icon, title, description, checked, onChange, disabled }: PrivacyToggleProps) {
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

export function PrivacySettings() {
  const [settings, setSettings] = useState<PrivacySettingsType>({
    profile_visibility: 'private',
    share_analytics: false,
    data_export_enabled: true,
  })
  const [isLoading, setIsLoading] = useState(false)
  const [isSaving, setIsSaving] = useState(false)
  const [isExporting, setIsExporting] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      setIsLoading(true)
      const data = await apiClient.getPrivacySettings()
      setSettings(data)
    } catch (err) {
      console.error('Failed to load privacy settings:', err)
      // Use defaults on error
    } finally {
      setIsLoading(false)
    }
  }

  const handleSave = async () => {
    try {
      setIsSaving(true)
      await apiClient.updatePrivacySettings(settings)
      setMessage({ type: 'success', text: 'Datenschutzeinstellungen gespeichert' })
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      console.error('Failed to save settings:', err)
      setMessage({ type: 'error', text: 'Fehler beim Speichern der Einstellungen' })
    } finally {
      setIsSaving(false)
    }
  }

  const handleExportData = async () => {
    try {
      setIsExporting(true)
      // TODO: Implement data export when backend endpoint is available
      setMessage({ type: 'success', text: 'Datenexport wird vorbereitet...' })
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      console.error('Failed to export data:', err)
      setMessage({ type: 'error', text: 'Fehler beim Exportieren der Daten' })
    } finally {
      setIsExporting(false)
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
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Datenschutz & Sicherheit</CardTitle>
          <CardDescription>
            Verwalten Sie Ihre Datenschutzeinstellungen und Sichtbarkeit
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Profile Visibility */}
          <div className="space-y-2">
            <div className="flex items-start gap-3 p-4 rounded-lg border border-border">
              <Eye className="h-5 w-5 mt-1 text-muted-foreground" />
              <div className="flex-1 space-y-2">
                <div className="font-medium">Profil-Sichtbarkeit</div>
                <p className="text-sm text-muted-foreground">
                  Steuern Sie, wer Ihr Profil sehen kann
                </p>
                <Select
                  value={settings.profile_visibility}
                  onChange={(e) =>
                    setSettings({
                      ...settings,
                      profile_visibility: e.target.value as 'public' | 'private' | 'therapist_only',
                    })
                  }
                  className="max-w-xs"
                >
                  <option value="private">Privat (nur ich)</option>
                  <option value="therapist_only">Nur mein Therapeut</option>
                  <option value="public">Öffentlich</option>
                </Select>
              </div>
            </div>
          </div>

          {/* Analytics Sharing */}
          <PrivacyToggle
            icon={<Share2 className="h-5 w-5" />}
            title="Analytik-Daten teilen"
            description="Anonyme Nutzungsdaten zur Verbesserung der App teilen"
            checked={settings.share_analytics}
            onChange={(checked) =>
              setSettings({ ...settings, share_analytics: checked })
            }
          />

          {/* Data Export */}
          <PrivacyToggle
            icon={<Download className="h-5 w-5" />}
            title="Datenexport aktivieren"
            description="Ermöglicht das Herunterladen Ihrer persönlichen Daten"
            checked={settings.data_export_enabled}
            onChange={(checked) =>
              setSettings({ ...settings, data_export_enabled: checked })
            }
          />

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

      {/* Data Export Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Daten exportieren
          </CardTitle>
          <CardDescription>
            Laden Sie eine Kopie Ihrer persönlichen Daten herunter
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Sie können alle Ihre persönlichen Daten als JSON-Datei exportieren. Dies umfasst
            Stimmungsdaten, Traumtagebücher, Therapienotizen und mehr.
          </p>
          <Button
            onClick={handleExportData}
            disabled={isExporting || !settings.data_export_enabled}
            variant="outline"
          >
            {isExporting ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Wird exportiert...
              </>
            ) : (
              <>
                <Download className="mr-2 h-4 w-4" />
                Daten exportieren
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Data Deletion Warning */}
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <Shield className="h-5 w-5" />
            Gefahr-Zone
          </CardTitle>
          <CardDescription>
            Unumkehrbare Aktionen mit Ihrem Account
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground">
            Das Löschen Ihres Accounts ist dauerhaft und kann nicht rückgängig gemacht werden.
            Alle Ihre Daten werden unwiederbringlich gelöscht.
          </p>
          <Button variant="destructive" disabled>
            Account löschen
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
