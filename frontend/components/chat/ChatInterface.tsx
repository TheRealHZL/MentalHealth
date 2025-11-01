'use client'

import { useEffect, useRef } from 'react'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ChatMessage } from './ChatMessage'
import { MessageInput } from './MessageInput'
import { MessageCircle, Bot } from 'lucide-react'
import type { AIChatSession } from '@/types'

interface ChatInterfaceProps {
  session: AIChatSession | null
  onSendMessage: (message: string) => Promise<any>
  isLoading: boolean
}

export function ChatInterface({ session, onSendMessage, isLoading }: ChatInterfaceProps) {
  const scrollRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [session?.messages])

  if (!session) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="text-center">
          <MessageCircle className="h-16 w-16 mx-auto mb-4 text-muted-foreground opacity-50" />
          <h2 className="text-2xl font-semibold mb-2">Willkommen beim AI Chat Assistant</h2>
          <p className="text-muted-foreground max-w-md">
            Starte eine neue Unterhaltung oder wähle eine bestehende aus der Liste.
            Ich bin hier, um dir bei deiner mentalen Gesundheit zu helfen.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-background">
      {/* Header */}
      <div className="p-4 border-b border-border bg-card">
        <h2 className="font-semibold text-lg">{session.title}</h2>
        <p className="text-sm text-muted-foreground">
          {session.messages.length} Nachrichten
        </p>
      </div>

      {/* Messages */}
      <ScrollArea ref={scrollRef} className="flex-1 p-4">
        <div className="space-y-4 max-w-4xl mx-auto">
          {session.messages.length === 0 ? (
            <div className="text-center py-12">
              <Bot className="h-12 w-12 mx-auto mb-3 text-primary opacity-50" />
              <p className="text-muted-foreground">
                Sende eine Nachricht, um die Unterhaltung zu starten.
              </p>
            </div>
          ) : (
            session.messages.map((message) => (
              <ChatMessage key={message.id} message={message} />
            ))
          )}
          {isLoading && (
            <ChatMessage
              message={{
                id: 'typing',
                role: 'assistant',
                content: '',
                timestamp: new Date().toISOString(),
              }}
              isTyping
            />
          )}
        </div>
      </ScrollArea>

      {/* Input */}
      <MessageInput
        onSend={onSendMessage}
        isLoading={isLoading}
        placeholder="Schreibe eine Nachricht... (Enter zum Senden, Shift+Enter für neue Zeile)"
      />
    </div>
  )
}
