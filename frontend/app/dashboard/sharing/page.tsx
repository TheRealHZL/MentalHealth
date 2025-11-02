'use client'

import { useState } from 'react'
import { ShareKeyManager } from '@/components/sharing/ShareKeyManager'
import { AccessLogViewer } from '@/components/sharing/AccessLogViewer'
import { SharedDataStatsComponent } from '@/components/sharing/SharedDataStats'
import { Key, Shield, Info } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

type Tab = 'keys' | 'logs' | 'info'

interface TabConfig {
  id: Tab
  label: string
  icon: React.ReactNode
}

const tabs: TabConfig[] = [
  {
    id: 'keys',
    label: 'Freigabeschlüssel',
    icon: <Key className="h-4 w-4" />,
  },
  {
    id: 'logs',
    label: 'Zugriffsprotokolle',
    icon: <Shield className="h-4 w-4" />,
  },
  {
    id: 'info',
    label: 'Informationen',
    icon: <Info className="h-4 w-4" />,
  },
]

export default function SharingPage() {
  const [activeTab, setActiveTab] = useState<Tab>('keys')

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Datenaustausch</h1>
        <p className="text-muted-foreground mt-2">
          Teilen Sie Ihre Gesundheitsdaten sicher mit Ihrem Therapeuten oder anderen Fachkräften
        </p>
      </div>

      {/* Stats */}
      <SharedDataStatsComponent />

      {/* Tabs */}
      <div className="border-b border-border">
        <div className="flex gap-1 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors border-b-2 ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:border-muted'
              }`}
            >
              {tab.icon}
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="pb-12">
        {activeTab === 'keys' && <ShareKeyManager />}
        {activeTab === 'logs' && <AccessLogViewer />}
        {activeTab === 'info' && <InfoTab />}
      </div>
    </div>
  )
}

function InfoTab() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Wie funktioniert der Datenaustausch?</CardTitle>
          <CardDescription>
            Verstehen Sie, wie Sie Ihre Daten sicher teilen können
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-start gap-3">
              <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                1
              </div>
              <div>
                <h3 className="font-medium">Freigabeschlüssel erstellen</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Erstellen Sie einen eindeutigen Schlüssel und wählen Sie aus, welche Datentypen Sie teilen möchten
                  (Stimmung, Träume, Therapienotizen, etc.).
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                2
              </div>
              <div>
                <h3 className="font-medium">Schlüssel teilen</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Kopieren Sie den generierten Schlüssel und senden Sie ihn sicher an Ihren Therapeuten oder die
                  gewünschte Person. Optional können Sie eine E-Mail-Adresse angeben, um den Zugriff einzuschränken.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <div className="mt-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground text-sm font-bold">
                3
              </div>
              <div>
                <h3 className="font-medium">Zugriffe überwachen</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Sehen Sie in den Zugriffsprotokollen, wann und von wem auf Ihre Daten zugegriffen wurde. Sie können
                  Schlüssel jederzeit widerrufen.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Sicherheit & Datenschutz
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-3 p-3 rounded-md bg-muted">
            <div className="text-green-600 dark:text-green-400 mt-0.5">✓</div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Ende-zu-Ende-Verschlüsselung</p>
              <p className="text-xs text-muted-foreground">
                Ihre Daten werden während der Übertragung verschlüsselt
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 rounded-md bg-muted">
            <div className="text-green-600 dark:text-green-400 mt-0.5">✓</div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Zeitlich begrenzte Schlüssel</p>
              <p className="text-xs text-muted-foreground">
                Alle Schlüssel haben ein Ablaufdatum und können jederzeit widerrufen werden
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 rounded-md bg-muted">
            <div className="text-green-600 dark:text-green-400 mt-0.5">✓</div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Granulare Berechtigungen</p>
              <p className="text-xs text-muted-foreground">
                Wählen Sie genau aus, welche Datentypen geteilt werden sollen
              </p>
            </div>
          </div>

          <div className="flex items-start gap-3 p-3 rounded-md bg-muted">
            <div className="text-green-600 dark:text-green-400 mt-0.5">✓</div>
            <div className="space-y-1">
              <p className="text-sm font-medium">Vollständige Transparenz</p>
              <p className="text-xs text-muted-foreground">
                Alle Zugriffe werden protokolliert und sind für Sie einsehbar
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card className="border-yellow-500 dark:border-yellow-700">
        <CardHeader>
          <CardTitle className="text-yellow-700 dark:text-yellow-500">Wichtige Hinweise</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            • Teilen Sie Ihre Freigabeschlüssel nur mit vertrauenswürdigen Personen und Fachkräften.
          </p>
          <p>
            • Überprüfen Sie regelmäßig Ihre aktiven Schlüssel und widerrufen Sie nicht mehr benötigte Schlüssel.
          </p>
          <p>
            • Kontrollieren Sie die Zugriffsprotokolle, um unerwartete Zugriffe zu erkennen.
          </p>
          <p>
            • Bei Verdacht auf unbefugten Zugriff widerrufen Sie sofort alle betroffenen Schlüssel und kontaktieren Sie den Support.
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
