'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Loader2, Check, AlertCircle, Lock, Eye, EyeOff, Shield } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { ChangePasswordRequest } from '@/types'

function PasswordStrengthIndicator({ password }: { password: string }) {
  const getStrength = (): { level: number; label: string; color: string } => {
    if (!password) return { level: 0, label: '', color: '' }

    let strength = 0
    if (password.length >= 8) strength++
    if (password.length >= 12) strength++
    if (/[a-z]/.test(password) && /[A-Z]/.test(password)) strength++
    if (/\d/.test(password)) strength++
    if (/[^a-zA-Z0-9]/.test(password)) strength++

    if (strength <= 2) return { level: 1, label: 'Schwach', color: 'bg-red-500' }
    if (strength <= 3) return { level: 2, label: 'Mittel', color: 'bg-yellow-500' }
    if (strength <= 4) return { level: 3, label: 'Gut', color: 'bg-blue-500' }
    return { level: 4, label: 'Sehr stark', color: 'bg-green-500' }
  }

  const strength = getStrength()
  if (!password) return null

  return (
    <div className="space-y-2">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((level) => (
          <div
            key={level}
            className={`h-1 flex-1 rounded-full transition-colors ${
              level <= strength.level ? strength.color : 'bg-muted'
            }`}
          />
        ))}
      </div>
      <p className="text-xs text-muted-foreground">
        Passwortstärke: <span className="font-medium">{strength.label}</span>
      </p>
    </div>
  )
}

export function SecuritySettings() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  const validatePassword = (): string | null => {
    if (!currentPassword) return 'Bitte geben Sie Ihr aktuelles Passwort ein'
    if (!newPassword) return 'Bitte geben Sie ein neues Passwort ein'
    if (newPassword.length < 8) return 'Passwort muss mindestens 8 Zeichen lang sein'
    if (newPassword === currentPassword) return 'Neues Passwort muss sich vom aktuellen unterscheiden'
    if (newPassword !== confirmPassword) return 'Passwörter stimmen nicht überein'
    return null
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const error = validatePassword()
    if (error) {
      setMessage({ type: 'error', text: error })
      return
    }

    try {
      setIsLoading(true)
      const data: ChangePasswordRequest = {
        current_password: currentPassword,
        new_password: newPassword,
      }
      await apiClient.changePassword(data)

      // Clear form
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')

      setMessage({ type: 'success', text: 'Passwort erfolgreich geändert' })
      setTimeout(() => setMessage(null), 3000)
    } catch (err: any) {
      console.error('Failed to change password:', err)
      const errorMsg = err.response?.data?.detail || 'Fehler beim Ändern des Passworts'
      setMessage({ type: 'error', text: errorMsg })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-5 w-5" />
            Passwort ändern
          </CardTitle>
          <CardDescription>
            Aktualisieren Sie Ihr Passwort, um Ihr Konto zu schützen
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Current Password */}
            <div className="space-y-2">
              <label htmlFor="currentPassword" className="text-sm font-medium">
                Aktuelles Passwort *
              </label>
              <div className="relative">
                <Input
                  id="currentPassword"
                  type={showCurrentPassword ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showCurrentPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* New Password */}
            <div className="space-y-2">
              <label htmlFor="newPassword" className="text-sm font-medium">
                Neues Passwort *
              </label>
              <div className="relative">
                <Input
                  id="newPassword"
                  type={showNewPassword ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showNewPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
              <PasswordStrengthIndicator password={newPassword} />
            </div>

            {/* Confirm Password */}
            <div className="space-y-2">
              <label htmlFor="confirmPassword" className="text-sm font-medium">
                Passwort bestätigen *
              </label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className="pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Password Requirements */}
            <div className="p-3 rounded-md bg-muted text-sm space-y-1">
              <p className="font-medium">Passwort-Anforderungen:</p>
              <ul className="list-disc list-inside text-muted-foreground space-y-1">
                <li>Mindestens 8 Zeichen</li>
                <li>Mindestens ein Großbuchstabe</li>
                <li>Mindestens ein Kleinbuchstabe</li>
                <li>Mindestens eine Zahl</li>
                <li>Mindestens ein Sonderzeichen (empfohlen)</li>
              </ul>
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

            {/* Submit */}
            <Button type="submit" disabled={isLoading} className="w-full md:w-auto">
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Wird geändert...
                </>
              ) : (
                'Passwort ändern'
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Security Info */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            Sicherheitsinformationen
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-3">
            <div className="flex items-start gap-3 p-3 rounded-md bg-muted">
              <Check className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Zwei-Faktor-Authentifizierung</p>
                <p className="text-xs text-muted-foreground">
                  Wird in einem zukünftigen Update verfügbar sein
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-md bg-muted">
              <Check className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Sichere Verbindung</p>
                <p className="text-xs text-muted-foreground">
                  Ihre Daten werden über HTTPS verschlüsselt übertragen
                </p>
              </div>
            </div>

            <div className="flex items-start gap-3 p-3 rounded-md bg-muted">
              <Check className="h-5 w-5 text-green-600 dark:text-green-400 mt-0.5" />
              <div className="space-y-1">
                <p className="text-sm font-medium">Passwort-Verschlüsselung</p>
                <p className="text-xs text-muted-foreground">
                  Ihr Passwort wird mit bcrypt verschlüsselt gespeichert
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
