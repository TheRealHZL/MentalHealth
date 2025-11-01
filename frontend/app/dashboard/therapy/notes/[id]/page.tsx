'use client'

import { useEffect, useState } from 'react'
import { useRouter, useParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { NoteEditor } from '@/components/therapy/NoteEditor'
import { TechniqueSelector } from '@/components/therapy/TechniqueSelector'
import { ArrowLeft, Save } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { TherapyNote, CreateTherapyNoteRequest } from '@/types'

export default function EditTherapyNotePage() {
  const router = useRouter()
  const params = useParams()
  const noteId = params.id as string

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [note, setNote] = useState<TherapyNote | null>(null)
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

  useEffect(() => {
    fetchNote()
  }, [noteId])

  const fetchNote = async () => {
    try {
      setIsLoading(true)
      const data = await apiClient.getTherapyNote(noteId)
      setNote(data)
      setFormData({
        title: data.title,
        content: data.content,
        technique: data.technique || '',
        session_date: data.session_date || '',
        mood_before: data.mood_before,
        mood_after: data.mood_after,
        tags: data.tags || [],
        is_private: data.is_private,
      })
    } catch (err) {
      console.error('Failed to fetch note:', err)
      alert('Fehler beim Laden der Notiz')
      router.push('/dashboard/therapy/notes')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.title || !formData.content) {
      alert('Bitte füllen Sie Titel und Inhalt aus')
      return
    }

    try {
      setIsSaving(true)
      await apiClient.updateTherapyNote(noteId, formData)
      router.push('/dashboard/therapy/notes')
    } catch (err) {
      console.error('Failed to update note:', err)
      alert('Fehler beim Aktualisieren der Notiz')
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-3xl font-bold">Therapienotiz bearbeiten</h1>
          <p className="text-muted-foreground">
            Aktualisieren Sie Ihre Notiz
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
