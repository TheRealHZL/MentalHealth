'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import {
  Key,
  Loader2,
  Check,
  AlertCircle,
  Copy,
  Trash2,
  Calendar,
  User,
  Activity,
  AlertTriangle
} from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { ShareKey, CreateShareKeyRequest, SharedDataType } from '@/types'
import { format, formatDistanceToNow } from 'date-fns'
import { de } from 'date-fns/locale'

const AVAILABLE_DATA_TYPES: SharedDataType[] = [
  {
    type: 'mood',
    label: 'Stimmungsdaten',
    description: 'Teilen Sie Ihre Stimmungseinträge und Trends',
    icon: '😊',
  },
  {
    type: 'dreams',
    label: 'Traumtagebuch',
    description: 'Teilen Sie Ihre Träume und Interpretationen',
    icon: '🌙',
  },
  {
    type: 'therapy_notes',
    label: 'Therapienotizen',
    description: 'Teilen Sie Ihre persönlichen Therapienotizen',
    icon: '📝',
  },
  {
    type: 'therapy_sessions',
    label: 'Therapiesitzungen',
    description: 'Teilen Sie Ihre Sitzungsverlauf und Fortschritt',
    icon: '🗓️',
  },
  {
    type: 'analytics',
    label: 'Analytik',
    description: 'Teilen Sie Ihre Wellness-Analysen und Berichte',
    icon: '📊',
  },
]

export function ShareKeyManager() {
  const [shareKeys, setShareKeys] = useState<ShareKey[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [showCreateForm, setShowCreateForm] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  // Form state
  const [recipientEmail, setRecipientEmail] = useState('')
  const [selectedDataTypes, setSelectedDataTypes] = useState<string[]>([])
  const [expiresInDays, setExpiresInDays] = useState<number>(30)
  const [copiedKeyId, setCopiedKeyId] = useState<string | null>(null)

  useEffect(() => {
    loadShareKeys()
  }, [])

  const loadShareKeys = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.getShareKeys(1, 50)
      setShareKeys(response.items)
    } catch (err) {
      console.error('Failed to load share keys:', err)
      setMessage({ type: 'error', text: 'Fehler beim Laden der Freigabeschlüssel' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleCreateShareKey = async () => {
    if (selectedDataTypes.length === 0) {
      setMessage({ type: 'error', text: 'Bitte wählen Sie mindestens einen Datentyp aus' })
      return
    }

    try {
      setIsCreating(true)
      const data: CreateShareKeyRequest = {
        recipient_email: recipientEmail || undefined,
        data_types: selectedDataTypes,
        expires_in_days: expiresInDays,
      }
      const newKey = await apiClient.createShareKey(data)
      setShareKeys([newKey, ...shareKeys])
      setMessage({ type: 'success', text: 'Freigabeschlüssel erfolgreich erstellt' })

      // Reset form
      setRecipientEmail('')
      setSelectedDataTypes([])
      setExpiresInDays(30)
      setShowCreateForm(false)

      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      console.error('Failed to create share key:', err)
      setMessage({ type: 'error', text: 'Fehler beim Erstellen des Freigabeschlüssels' })
    } finally {
      setIsCreating(false)
    }
  }

  const handleRevokeKey = async (id: string) => {
    if (!confirm('Möchten Sie diesen Freigabeschlüssel wirklich widerrufen?')) {
      return
    }

    try {
      await apiClient.revokeShareKey(id)
      setShareKeys(shareKeys.filter((key) => key.id !== id))
      setMessage({ type: 'success', text: 'Freigabeschlüssel widerrufen' })
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      console.error('Failed to revoke share key:', err)
      setMessage({ type: 'error', text: 'Fehler beim Widerrufen des Freigabeschlüssels' })
    }
  }

  const handleCopyKey = async (key: string, id: string) => {
    try {
      await navigator.clipboard.writeText(key)
      setCopiedKeyId(id)
      setTimeout(() => setCopiedKeyId(null), 2000)
    } catch (err) {
      console.error('Failed to copy key:', err)
    }
  }

  const toggleDataType = (type: string) => {
    if (selectedDataTypes.includes(type)) {
      setSelectedDataTypes(selectedDataTypes.filter((t) => t !== type))
    } else {
      setSelectedDataTypes([...selectedDataTypes, type])
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Key className="h-5 w-5" />
                Freigabeschlüssel
              </CardTitle>
              <CardDescription>
                Erstellen und verwalten Sie Schlüssel zum Teilen Ihrer Daten
              </CardDescription>
            </div>
            <Button onClick={() => setShowCreateForm(!showCreateForm)}>
              {showCreateForm ? 'Abbrechen' : 'Neuer Schlüssel'}
            </Button>
          </div>
        </CardHeader>

        {/* Create Form */}
        {showCreateForm && (
          <CardContent className="border-t border-border pt-6">
            <div className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="recipientEmail" className="text-sm font-medium">
                  E-Mail des Empfängers (optional)
                </label>
                <Input
                  id="recipientEmail"
                  type="email"
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  placeholder="therapeut@example.com"
                />
                <p className="text-xs text-muted-foreground">
                  Wenn angegeben, kann nur diese E-Mail-Adresse den Schlüssel verwenden
                </p>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Zu teilende Daten</label>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {AVAILABLE_DATA_TYPES.map((dataType) => (
                    <button
                      key={dataType.type}
                      type="button"
                      onClick={() => toggleDataType(dataType.type)}
                      className={`flex items-start gap-3 p-3 rounded-lg border-2 transition-all text-left ${
                        selectedDataTypes.includes(dataType.type)
                          ? 'border-primary bg-primary/5'
                          : 'border-border hover:border-muted-foreground'
                      }`}
                    >
                      <span className="text-2xl">{dataType.icon}</span>
                      <div className="flex-1">
                        <div className="font-medium text-sm">{dataType.label}</div>
                        <p className="text-xs text-muted-foreground mt-0.5">
                          {dataType.description}
                        </p>
                      </div>
                      {selectedDataTypes.includes(dataType.type) && (
                        <Check className="h-4 w-4 text-primary mt-1" />
                      )}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-2">
                <label htmlFor="expiresInDays" className="text-sm font-medium">
                  Gültigkeitsdauer
                </label>
                <Select
                  id="expiresInDays"
                  value={expiresInDays.toString()}
                  onChange={(e) => setExpiresInDays(Number(e.target.value))}
                >
                  <option value="7">7 Tage</option>
                  <option value="30">30 Tage</option>
                  <option value="90">90 Tage</option>
                  <option value="180">180 Tage</option>
                  <option value="365">1 Jahr</option>
                </Select>
              </div>

              <Button onClick={handleCreateShareKey} disabled={isCreating} className="w-full">
                {isCreating ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Wird erstellt...
                  </>
                ) : (
                  'Freigabeschlüssel erstellen'
                )}
              </Button>
            </div>
          </CardContent>
        )}
      </Card>

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

      {/* Share Keys List */}
      {isLoading ? (
        <Card>
          <CardContent className="py-12 flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </CardContent>
        </Card>
      ) : shareKeys.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center text-muted-foreground">
            <Key className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p>Noch keine Freigabeschlüssel erstellt</p>
            <p className="text-sm mt-2">
              Erstellen Sie einen Schlüssel, um Ihre Daten zu teilen
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {shareKeys.map((shareKey) => (
            <Card key={shareKey.id}>
              <CardContent className="p-4">
                <div className="space-y-3">
                  {/* Key Header */}
                  <div className="flex items-start justify-between gap-4">
                    <div className="space-y-1 flex-1">
                      <div className="flex items-center gap-2">
                        <Key className="h-4 w-4 text-muted-foreground" />
                        <code className="text-sm bg-muted px-2 py-1 rounded font-mono">
                          {shareKey.key.substring(0, 32)}...
                        </code>
                        <button
                          onClick={() => handleCopyKey(shareKey.key, shareKey.id)}
                          className="p-1 hover:bg-muted rounded transition-colors"
                          title="Schlüssel kopieren"
                        >
                          {copiedKeyId === shareKey.id ? (
                            <Check className="h-4 w-4 text-green-600" />
                          ) : (
                            <Copy className="h-4 w-4 text-muted-foreground" />
                          )}
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {shareKey.is_active ? (
                        <span className="text-xs px-2 py-1 rounded-full bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300">
                          Aktiv
                        </span>
                      ) : (
                        <span className="text-xs px-2 py-1 rounded-full bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300">
                          Widerrufen
                        </span>
                      )}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRevokeKey(shareKey.id)}
                        disabled={!shareKey.is_active}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>

                  {/* Key Info */}
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                    {shareKey.recipient_email && (
                      <div className="flex items-center gap-2 text-muted-foreground">
                        <User className="h-4 w-4" />
                        <span>{shareKey.recipient_email}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Calendar className="h-4 w-4" />
                      <span>
                        {shareKey.expires_at
                          ? `Läuft ab ${formatDistanceToNow(new Date(shareKey.expires_at), {
                              addSuffix: true,
                              locale: de,
                            })}`
                          : 'Kein Ablaufdatum'}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Activity className="h-4 w-4" />
                      <span>{shareKey.access_count} Zugriffe</span>
                    </div>
                  </div>

                  {/* Shared Data Types */}
                  <div className="flex flex-wrap gap-2">
                    {shareKey.data_types.map((type) => {
                      const dataType = AVAILABLE_DATA_TYPES.find((dt) => dt.type === type)
                      return (
                        <span
                          key={type}
                          className="text-xs px-2 py-1 rounded-full bg-muted"
                        >
                          {dataType?.icon} {dataType?.label || type}
                        </span>
                      )
                    })}
                  </div>

                  {/* Expiry Warning */}
                  {shareKey.expires_at &&
                    new Date(shareKey.expires_at) < new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) &&
                    shareKey.is_active && (
                      <div className="flex items-center gap-2 p-2 rounded-md bg-yellow-50 dark:bg-yellow-950 text-yellow-900 dark:text-yellow-100 text-xs">
                        <AlertTriangle className="h-4 w-4" />
                        <span>
                          Dieser Schlüssel läuft bald ab (
                          {format(new Date(shareKey.expires_at), 'dd.MM.yyyy', { locale: de })})
                        </span>
                      </div>
                    )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
