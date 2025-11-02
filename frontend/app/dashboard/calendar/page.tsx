'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import {
  Calendar as CalendarIcon,
  Plus,
  ChevronLeft,
  ChevronRight,
  Loader2,
  Clock,
  X,
  Check
} from 'lucide-react'
import { apiClient } from '@/lib/api'
import type { CalendarEvent, CreateCalendarEventRequest } from '@/types'
import { format, startOfWeek, addDays, isSameDay, parseISO, addWeeks, subWeeks } from 'date-fns'
import { de } from 'date-fns/locale'

const EVENT_COLORS: Record<string, string> = {
  therapy_session: '#3B82F6',
  reminder: '#EF4444',
  personal: '#8B5CF6',
  medication: '#10B981',
  appointment: '#F59E0B',
}

const EVENT_LABELS: Record<string, string> = {
  therapy_session: 'Therapiesitzung',
  reminder: 'Erinnerung',
  personal: 'Persönlich',
  medication: 'Medikament',
  appointment: 'Termin',
}

export default function CalendarPage() {
  const [currentWeek, setCurrentWeek] = useState(startOfWeek(new Date(), { weekStartsOn: 1 }))
  const [events, setEvents] = useState<CalendarEvent[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [selectedDate, setSelectedDate] = useState<Date | null>(null)
  const [formData, setFormData] = useState<CreateCalendarEventRequest>({
    title: '',
    description: '',
    start_time: '',
    end_time: '',
    event_type: 'personal',
  })

  useEffect(() => {
    loadEvents()
  }, [])

  const loadEvents = async () => {
    try {
      setIsLoading(true)
      // Load from localStorage first to include user-created events
      const stored = typeof window !== 'undefined' ? localStorage.getItem('calendar_events') : null
      const localEvents = stored ? JSON.parse(stored) : []

      const apiEvents = await apiClient.getCalendarEvents()

      // Merge and deduplicate
      const allEvents = [...apiEvents, ...localEvents]
      const uniqueEvents = Array.from(
        new Map(allEvents.map(e => [e.id, e])).values()
      )

      setEvents(uniqueEvents)
    } catch (err) {
      console.error('Failed to load events:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const weekDays = Array.from({ length: 7 }, (_, i) => addDays(currentWeek, i))

  const getEventsForDay = (date: Date) => {
    return events.filter((event) => {
      try {
        return isSameDay(parseISO(event.start_time), date)
      } catch {
        return false
      }
    })
  }

  const handleCreateEvent = async () => {
    if (!formData.title || !selectedDate) return

    const startTime = new Date(selectedDate)
    startTime.setHours(9, 0, 0, 0)

    const endTime = new Date(selectedDate)
    endTime.setHours(10, 0, 0, 0)

    const eventData: CreateCalendarEventRequest = {
      ...formData,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
    }

    try {
      const newEvent = await apiClient.createCalendarEvent(eventData)
      setEvents([...events, newEvent])
      setShowModal(false)
      setFormData({
        title: '',
        description: '',
        start_time: '',
        end_time: '',
        event_type: 'personal',
      })
      setSelectedDate(null)
    } catch (err) {
      console.error('Failed to create event:', err)
    }
  }

  const handleDeleteEvent = async (id: string) => {
    if (!confirm('Termin wirklich löschen?')) return

    try {
      await apiClient.deleteCalendarEvent(id)
      setEvents(events.filter(e => e.id !== id))
    } catch (err) {
      console.error('Failed to delete event:', err)
    }
  }

  const openCreateModal = (date: Date) => {
    setSelectedDate(date)
    setShowModal(true)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Wochenplaner</h1>
          <p className="text-muted-foreground mt-2">
            Verwalten Sie Ihre Termine und Erinnerungen
          </p>
        </div>
        <Button onClick={() => setShowModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          Neuer Termin
        </Button>
      </div>

      {/* Week Navigation */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentWeek(subWeeks(currentWeek, 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="text-center">
              <div className="font-medium">
                {format(currentWeek, 'MMMM yyyy', { locale: de })}
              </div>
              <div className="text-sm text-muted-foreground">
                KW {format(currentWeek, 'w', { locale: de })}
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentWeek(addWeeks(currentWeek, 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Calendar Grid */}
      {isLoading ? (
        <Card>
          <CardContent className="py-12 flex justify-center">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-7 gap-4">
          {weekDays.map((day, index) => {
            const dayEvents = getEventsForDay(day)
            const isToday = isSameDay(day, new Date())

            return (
              <Card
                key={index}
                className={`${isToday ? 'border-primary border-2' : ''}`}
              >
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">
                    <div className="flex items-center justify-between">
                      <span>{format(day, 'EEE', { locale: de })}</span>
                      <span className={`text-lg ${isToday ? 'text-primary font-bold' : ''}`}>
                        {format(day, 'd')}
                      </span>
                    </div>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {dayEvents.length === 0 ? (
                    <button
                      onClick={() => openCreateModal(day)}
                      className="w-full p-2 text-xs text-muted-foreground border-2 border-dashed border-muted-foreground/20 rounded hover:border-primary hover:text-primary transition-colors"
                    >
                      <Plus className="h-3 w-3 mx-auto" />
                    </button>
                  ) : (
                    dayEvents.map((event) => (
                      <div
                        key={event.id}
                        className="p-2 rounded text-xs group relative"
                        style={{
                          backgroundColor: event.color || EVENT_COLORS[event.event_type] || '#6B7280',
                          color: 'white',
                        }}
                      >
                        <button
                          onClick={() => handleDeleteEvent(event.id)}
                          className="absolute top-1 right-1 opacity-0 group-hover:opacity-100 transition-opacity p-0.5 rounded bg-white/20 hover:bg-white/40"
                        >
                          <X className="h-3 w-3" />
                        </button>
                        <div className="font-medium truncate pr-5">{event.title}</div>
                        <div className="flex items-center gap-1 mt-1 opacity-90">
                          <Clock className="h-3 w-3" />
                          <span>{format(parseISO(event.start_time), 'HH:mm')}</span>
                        </div>
                      </div>
                    ))
                  )}
                </CardContent>
              </Card>
            )
          })}
        </div>
      )}

      {/* Create Event Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-md">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle>Neuer Termin</CardTitle>
                <button onClick={() => setShowModal(false)}>
                  <X className="h-5 w-5" />
                </button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Titel *</label>
                <Input
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  placeholder="z.B. Therapiesitzung"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Beschreibung</label>
                <Input
                  value={formData.description || ''}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Optional"
                />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium">Typ</label>
                <Select
                  value={formData.event_type}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      event_type: e.target.value as any,
                    })
                  }
                >
                  {Object.entries(EVENT_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" onClick={() => setShowModal(false)} className="flex-1">
                  Abbrechen
                </Button>
                <Button onClick={handleCreateEvent} disabled={!formData.title} className="flex-1">
                  <Check className="mr-2 h-4 w-4" />
                  Erstellen
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
