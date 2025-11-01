'use client'

import { useState } from 'react'
import { ProfileEditor } from '@/components/settings/ProfileEditor'
import { NotificationSettings } from '@/components/settings/NotificationSettings'
import { PrivacySettings } from '@/components/settings/PrivacySettings'
import { SecuritySettings } from '@/components/settings/SecuritySettings'
import { User, Bell, Shield, Lock } from 'lucide-react'

type Tab = 'profile' | 'notifications' | 'privacy' | 'security'

interface TabConfig {
  id: Tab
  label: string
  icon: React.ReactNode
  component: React.ReactNode
}

const tabs: TabConfig[] = [
  {
    id: 'profile',
    label: 'Profil',
    icon: <User className="h-4 w-4" />,
    component: <ProfileEditor />,
  },
  {
    id: 'notifications',
    label: 'Benachrichtigungen',
    icon: <Bell className="h-4 w-4" />,
    component: <NotificationSettings />,
  },
  {
    id: 'privacy',
    label: 'Datenschutz',
    icon: <Shield className="h-4 w-4" />,
    component: <PrivacySettings />,
  },
  {
    id: 'security',
    label: 'Sicherheit',
    icon: <Lock className="h-4 w-4" />,
    component: <SecuritySettings />,
  },
]

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('profile')

  const activeTabConfig = tabs.find((tab) => tab.id === activeTab)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Einstellungen</h1>
        <p className="text-muted-foreground mt-2">
          Verwalten Sie Ihr Konto und Ihre Präferenzen
        </p>
      </div>

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
      <div className="pb-12">{activeTabConfig?.component}</div>
    </div>
  )
}
