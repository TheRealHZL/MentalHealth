'use client'

import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Search, FileText, Calendar, Tag, Trash2, Edit } from 'lucide-react'
import { formatDate } from '@/lib/utils'
import type { TherapyNote } from '@/types'
import Link from 'next/link'

interface NotesListProps {
  notes: TherapyNote[]
  onDelete?: (id: string) => void
}

export function NotesList({ notes, onDelete }: NotesListProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [filterTechnique, setFilterTechnique] = useState('')

  const filteredNotes = notes.filter(note => {
    const matchesSearch = note.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         note.content.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesTechnique = !filterTechnique || note.technique === filterTechnique
    return matchesSearch && matchesTechnique
  })

  const techniques = Array.from(new Set(notes.map(n => n.technique).filter(Boolean)))

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Notizen durchsuchen..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9"
          />
        </div>
        <select
          value={filterTechnique}
          onChange={(e) => setFilterTechnique(e.target.value)}
          className="px-3 py-2 border border-input rounded-md bg-background"
        >
          <option value="">Alle Techniken</option>
          {techniques.map(tech => (
            <option key={tech} value={tech}>{tech}</option>
          ))}
        </select>
      </div>

      {/* Notes Grid */}
      {filteredNotes.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <FileText className="h-12 w-12 mx-auto mb-3 text-muted-foreground opacity-50" />
            <p className="text-muted-foreground">
              {searchTerm || filterTechnique ? 'Keine passenden Notizen gefunden' : 'Noch keine Notizen vorhanden'}
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredNotes.map((note) => (
            <Card key={note.id} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between gap-2">
                  <CardTitle className="text-lg line-clamp-2">{note.title}</CardTitle>
                  <div className="flex gap-1">
                    <Link href={`/dashboard/therapy/notes/${note.id}`}>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <Edit className="h-4 w-4" />
                      </Button>
                    </Link>
                    {onDelete && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 hover:bg-destructive hover:text-destructive-foreground"
                        onClick={() => onDelete(note.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div
                  className="text-sm text-muted-foreground line-clamp-3"
                  dangerouslySetInnerHTML={{ __html: note.content }}
                />

                <div className="space-y-2 text-xs text-muted-foreground">
                  {note.technique && (
                    <div className="flex items-center gap-2">
                      <Tag className="h-3 w-3" />
                      <span>{note.technique}</span>
                    </div>
                  )}
                  {note.session_date && (
                    <div className="flex items-center gap-2">
                      <Calendar className="h-3 w-3" />
                      <span>{formatDate(note.session_date)}</span>
                    </div>
                  )}
                  <div className="flex items-center justify-between pt-2 border-t border-border">
                    <span>Erstellt: {formatDate(note.created_at)}</span>
                    {note.mood_before && note.mood_after && (
                      <span>
                        Stimmung: {note.mood_before} → {note.mood_after}
                      </span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
