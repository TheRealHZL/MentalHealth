'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { NotesList } from '@/components/therapy/NotesList'
import { Plus, FileText } from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { TherapyNote } from '@/types'

export default function TherapyNotesPage() {
  const router = useRouter()
  const [notes, setNotes] = useState<TherapyNote[]>([])
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    fetchNotes()
  }, [])

  const fetchNotes = async () => {
    try {
      setIsLoading(true)
      const response = await apiClient.getTherapyNotes(1, 100)
      setNotes(response.items)
    } catch (err) {
      console.error('Failed to fetch notes:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Möchten Sie diese Notiz wirklich löschen?')) return

    try {
      await apiClient.deleteTherapyNote(id)
      setNotes(notes.filter(n => n.id !== id))
    } catch (err) {
      console.error('Failed to delete note:', err)
      alert('Fehler beim Löschen der Notiz')
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
    <div className="container mx-auto px-4 py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="p-2 bg-primary/10 rounded-lg">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-3xl font-bold">Therapienotizen</h1>
            <p className="text-muted-foreground">
              Dokumentieren Sie Ihre Therapiesitzungen und Fortschritte
            </p>
          </div>
        </div>
        <Button onClick={() => router.push('/dashboard/therapy/notes/new')}>
          <Plus className="h-4 w-4 mr-2" />
          Neue Notiz
        </Button>
      </div>

      {/* Notes List */}
      <NotesList notes={notes} onDelete={handleDelete} />
    </div>
  )
}
