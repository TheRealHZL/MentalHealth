'use client'

import { useState, useRef, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import { User, Camera, Loader2, Check, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { User as UserType, UpdateProfileRequest } from '@/types'

const TIMEZONES = [
  'Europe/Berlin',
  'Europe/London',
  'America/New_York',
  'America/Los_Angeles',
  'Asia/Tokyo',
  'Australia/Sydney',
]

const LANGUAGES = [
  { code: 'de', name: 'Deutsch' },
  { code: 'en', name: 'English' },
]

export function ProfileEditor() {
  const [user, setUser] = useState<UserType | null>(null)
  const [firstName, setFirstName] = useState('')
  const [lastName, setLastName] = useState('')
  const [email, setEmail] = useState('')
  const [timezone, setTimezone] = useState('Europe/Berlin')
  const [language, setLanguage] = useState('de')
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isUploading, setIsUploading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    loadProfile()
  }, [])

  const loadProfile = async () => {
    try {
      setIsLoading(true)
      const profile = await apiClient.getProfile()
      setUser(profile)
      setFirstName(profile.first_name)
      setLastName(profile.last_name)
      setEmail(profile.email)
      setTimezone(profile.timezone || 'Europe/Berlin')
      setLanguage(profile.language || 'de')
      setAvatarPreview(profile.avatar_url || null)
    } catch (err) {
      console.error('Failed to load profile:', err)
      setMessage({ type: 'error', text: 'Fehler beim Laden des Profils' })
    } finally {
      setIsLoading(false)
    }
  }

  const handleAvatarClick = () => {
    fileInputRef.current?.click()
  }

  const handleAvatarChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setMessage({ type: 'error', text: 'Bitte wählen Sie eine Bilddatei' })
      return
    }

    // Validate file size (max 5MB)
    if (file.size > 5 * 1024 * 1024) {
      setMessage({ type: 'error', text: 'Bild ist zu groß (max. 5MB)' })
      return
    }

    // Preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setAvatarPreview(reader.result as string)
    }
    reader.readAsDataURL(file)

    // Upload
    try {
      setIsUploading(true)
      const updatedUser = await apiClient.uploadAvatar(file)
      setUser(updatedUser)
      setMessage({ type: 'success', text: 'Avatar erfolgreich hochgeladen' })
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      console.error('Failed to upload avatar:', err)
      setMessage({ type: 'error', text: 'Fehler beim Hochladen des Avatars' })
    } finally {
      setIsUploading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!firstName.trim() || !lastName.trim()) {
      setMessage({ type: 'error', text: 'Bitte füllen Sie alle Pflichtfelder aus' })
      return
    }

    try {
      setIsLoading(true)
      const data: UpdateProfileRequest = {
        first_name: firstName,
        last_name: lastName,
        timezone,
        language,
      }
      const updatedUser = await apiClient.updateProfile(data)
      setUser(updatedUser)

      // Update localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('user', JSON.stringify(updatedUser))
      }

      setMessage({ type: 'success', text: 'Profil erfolgreich aktualisiert' })
      setTimeout(() => setMessage(null), 3000)
    } catch (err) {
      console.error('Failed to update profile:', err)
      setMessage({ type: 'error', text: 'Fehler beim Aktualisieren des Profils' })
    } finally {
      setIsLoading(false)
    }
  }

  if (isLoading && !user) {
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
        <CardTitle>Profil bearbeiten</CardTitle>
        <CardDescription>
          Aktualisieren Sie Ihre persönlichen Informationen
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Avatar */}
          <div className="flex items-center gap-4">
            <div className="relative">
              <div className="h-24 w-24 rounded-full bg-muted flex items-center justify-center overflow-hidden border-2 border-border">
                {avatarPreview ? (
                  <img src={avatarPreview} alt="Avatar" className="h-full w-full object-cover" />
                ) : (
                  <User className="h-12 w-12 text-muted-foreground" />
                )}
              </div>
              <button
                type="button"
                onClick={handleAvatarClick}
                disabled={isUploading}
                className="absolute bottom-0 right-0 h-8 w-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center hover:bg-primary/90 transition-colors disabled:opacity-50"
              >
                {isUploading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Camera className="h-4 w-4" />
                )}
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleAvatarChange}
                className="hidden"
              />
            </div>
            <div>
              <p className="text-sm font-medium">Profilbild</p>
              <p className="text-xs text-muted-foreground">
                JPG, PNG oder GIF (max. 5MB)
              </p>
            </div>
          </div>

          {/* Name Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label htmlFor="firstName" className="text-sm font-medium">
                Vorname *
              </label>
              <Input
                id="firstName"
                value={firstName}
                onChange={(e) => setFirstName(e.target.value)}
                placeholder="Max"
                required
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="lastName" className="text-sm font-medium">
                Nachname *
              </label>
              <Input
                id="lastName"
                value={lastName}
                onChange={(e) => setLastName(e.target.value)}
                placeholder="Mustermann"
                required
              />
            </div>
          </div>

          {/* Email (read-only) */}
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">
              E-Mail-Adresse
            </label>
            <Input
              id="email"
              type="email"
              value={email}
              disabled
              className="bg-muted"
            />
            <p className="text-xs text-muted-foreground">
              E-Mail-Adresse kann nicht geändert werden
            </p>
          </div>

          {/* Timezone */}
          <div className="space-y-2">
            <label htmlFor="timezone" className="text-sm font-medium">
              Zeitzone
            </label>
            <Select
              id="timezone"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
            >
              {TIMEZONES.map((tz) => (
                <option key={tz} value={tz}>
                  {tz}
                </option>
              ))}
            </Select>
          </div>

          {/* Language */}
          <div className="space-y-2">
            <label htmlFor="language" className="text-sm font-medium">
              Sprache
            </label>
            <Select
              id="language"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              {LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.name}
                </option>
              ))}
            </Select>
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
                Wird gespeichert...
              </>
            ) : (
              'Änderungen speichern'
            )}
          </Button>
        </form>
      </CardContent>
    </Card>
  )
}
