'use client'

import { Button } from '@/components/ui/button'
import { ScrollArea } from '@/components/ui/scroll-area'
import { MessageCircle, Plus, Trash2 } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'
import { de } from 'date-fns/locale'
import type { AIChatSession } from '@/types'

interface ChatSessionListProps {
  sessions: AIChatSession[]
  currentSessionId?: string
  onSelectSession: (sessionId: string) => void
  onCreateSession: () => void
  onDeleteSession: (sessionId: string) => void
}

export function ChatSessionList({
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
}: ChatSessionListProps) {
  return (
    <div className="w-full lg:w-80 border-r border-border bg-card flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <Button onClick={onCreateSession} className="w-full" size="sm">
          <Plus className="h-4 w-4 mr-2" />
          Neue Unterhaltung
        </Button>
      </div>

      {/* Sessions List */}
      <ScrollArea className="flex-1">
        <div className="p-2 space-y-2">
          {sessions.length === 0 ? (
            <div className="text-center py-8 px-4 text-muted-foreground">
              <MessageCircle className="h-12 w-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">Noch keine Unterhaltungen</p>
              <p className="text-xs mt-1">Starte eine neue Unterhaltung</p>
            </div>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`group relative p-3 rounded-lg cursor-pointer transition-colors ${
                  currentSessionId === session.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-muted'
                }`}
                onClick={() => onSelectSession(session.id)}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-sm truncate">{session.title}</h3>
                    {session.last_message_preview && (
                      <p className="text-xs opacity-70 truncate mt-1">
                        {session.last_message_preview}
                      </p>
                    )}
                    <p className="text-xs opacity-60 mt-1">
                      {formatDistanceToNow(new Date(session.updated_at), {
                        addSuffix: true,
                        locale: de,
                      })}
                    </p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className={`h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity ${
                      currentSessionId === session.id
                        ? 'text-primary-foreground hover:bg-primary-foreground/20'
                        : 'hover:bg-destructive hover:text-destructive-foreground'
                    }`}
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteSession(session.id)
                    }}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  )
}
