'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useChat } from '@/hooks/useChat'
import { ChatInterface } from '@/components/chat/ChatInterface'
import { ChatSessionList } from '@/components/chat/ChatSessionList'
import { MessageSquare, Menu, X } from 'lucide-react'
import { Button } from '@/components/ui/button'

export default function ChatPage() {
  const router = useRouter()
  const {
    sessions,
    currentSession,
    isLoading,
    createSession,
    deleteSession,
    sendMessage,
    setCurrentSession,
  } = useChat()

  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)

  // Auto-create first session if none exists
  useEffect(() => {
    if (sessions.length === 0) {
      createSession('Erste Unterhaltung')
    }
  }, [])

  const handleSelectSession = (sessionId: string) => {
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      setCurrentSession(session)
      setIsMobileSidebarOpen(false)
    }
  }

  const handleCreateSession = () => {
    const newSession = createSession(`Unterhaltung ${sessions.length + 1}`)
    setCurrentSession(newSession)
    setIsMobileSidebarOpen(false)
  }

  const handleDeleteSession = (sessionId: string) => {
    deleteSession(sessionId)
    if (currentSession?.id === sessionId && sessions.length > 1) {
      const remainingSessions = sessions.filter(s => s.id !== sessionId)
      if (remainingSessions.length > 0) {
        setCurrentSession(remainingSessions[0])
      }
    }
  }

  const handleSendMessage = async (message: string) => {
    await sendMessage(message, currentSession?.id)
  }

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] lg:h-[calc(100vh-2rem)]">
      {/* Mobile Header */}
      <div className="lg:hidden flex items-center justify-between p-4 border-b border-border bg-card">
        <div className="flex items-center space-x-2">
          <MessageSquare className="h-5 w-5 text-primary" />
          <h1 className="font-semibold">AI Chat Assistant</h1>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
        >
          {isMobileSidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </Button>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Desktop always visible, Mobile conditional */}
        <div
          className={`${
            isMobileSidebarOpen ? 'block' : 'hidden'
          } lg:block fixed lg:relative inset-0 lg:inset-auto z-40 lg:z-auto`}
        >
          <ChatSessionList
            sessions={sessions}
            currentSessionId={currentSession?.id}
            onSelectSession={handleSelectSession}
            onCreateSession={handleCreateSession}
            onDeleteSession={handleDeleteSession}
          />
        </div>

        {/* Mobile Overlay */}
        {isMobileSidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-30 lg:hidden"
            onClick={() => setIsMobileSidebarOpen(false)}
          />
        )}

        {/* Chat Interface */}
        <ChatInterface
          session={currentSession}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
        />
      </div>
    </div>
  )
}
