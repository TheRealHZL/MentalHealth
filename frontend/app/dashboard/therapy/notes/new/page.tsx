'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { NoteEditor } from '@/components/therapy/NoteEditor'
import { TechniqueSelector } from '@/components/therapy/TechniqueSelector'
import { ArrowLeft, Save } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { CreateTherapyNoteRequest } from '@/types'

export default function NewTherapyNotePage() {
  const router = useRouter()
  const [isSaving, setIsSaving] = useState(false)
  const [formData, setFormData] = useState<CreateTherapyNoteRequest>({
    title: '',
    content: '',
    technique: '',
    session_date: '',
    mood_before: undefined,
    mood_after: undefined,
    tags: [],
    is_private: true,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.title || !formData.content) {
      alert('Bitte füllen Sie Titel und Inhalt aus')
      return
    }

    try {
      setIsSaving(true)
      await apiClient.createTherapyNote(formData)
      router.push('/dashboard/therapy/notes')
    } catch (err) {
      console.error('Failed to create note:', err)
      alert('Fehler beim Erstellen der Notiz')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Neue Therapienotiz</h1>
          <p className="text-muted-foreground">
            Dokumentieren Sie Ihre Sitzung und Erkenntnisse
          </p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>Grundinformationen</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">
                Titel *
              </label>
              <Input
                placeholder="z.B. Sitzung am 15. Januar 2025"
                value={formData.title}
                onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                required
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Therapietechnik
                </label>
                <TechniqueSelector
                  value={formData.technique}
                  onChange={(value) => setFormData({ ...formData, technique: value })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Sitzungsdatum
                </label>
                <Input
                  type="date"
                  value={formData.session_date}
                  onChange={(e) => setFormData({ ...formData, session_date: e.target.value })}
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">
                  Stimmung vorher (0-10)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  placeholder="Optional"
                  value={formData.mood_before || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    mood_before: e.target.value ? Number(e.target.value) : undefined
                  })}
                />
              </div>

              <div>
                <label className="text-sm font-medium mb-2 block">
                  Stimmung nachher (0-10)
                </label>
                <Input
                  type="number"
                  min="0"
                  max="10"
                  placeholder="Optional"
                  value={formData.mood_after || ''}
                  onChange={(e) => setFormData({
                    ...formData,
                    mood_after: e.target.value ? Number(e.target.value) : undefined
                  })}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Notizinhalt *</CardTitle>
          </CardHeader>
          <CardContent>
            <NoteEditor
              content={formData.content}
              onChange={(content) => setFormData({ ...formData, content })}
              placeholder="Beschreiben Sie Ihre Sitzung, Gedanken und Erkenntnisse..."
            />
          </CardContent>
        </Card>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <Button type="button" variant="outline" onClick={() => router.back()}>
            Abbrechen
          </Button>
          <Button type="submit" disabled={isSaving}>
            {isSaving ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                Speichern...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Speichern
              </>
            )}
          </Button>
        </div>
      </form>
    </div>
  )
}
