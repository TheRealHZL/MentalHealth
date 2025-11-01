'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'
import type { AIChatSession, AIChatMessage, AIChatRequest } from '@/types'

export function useChat() {
  const [sessions, setSessions] = useState<AIChatSession[]>([])
  const [currentSession, setCurrentSession] = useState<AIChatSession | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load sessions from localStorage
  useEffect(() => {
    const loadSessions = () => {
      try {
        const stored = localStorage.getItem('chat_sessions')
        if (stored) {
          const parsed = JSON.parse(stored)
          setSessions(parsed)
        }
      } catch (err) {
        console.error('Failed to load chat sessions:', err)
      }
    }
    loadSessions()
  }, [])

  // Save sessions to localStorage
  const saveSessions = (updatedSessions: AIChatSession[]) => {
    try {
      localStorage.setItem('chat_sessions', JSON.stringify(updatedSessions))
      setSessions(updatedSessions)
    } catch (err) {
      console.error('Failed to save chat sessions:', err)
    }
  }

  // Create new session
  const createSession = (title?: string): AIChatSession => {
    const newSession: AIChatSession = {
      id: `session_${Date.now()}`,
      title: title || 'Neue Unterhaltung',
      messages: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    const updatedSessions = [newSession, ...sessions]
    saveSessions(updatedSessions)
    setCurrentSession(newSession)
    return newSession
  }

  // Get session by ID
  const getSession = (sessionId: string): AIChatSession | undefined => {
    return sessions.find(s => s.id === sessionId)
  }

  // Update session
  const updateSession = (sessionId: string, updates: Partial<AIChatSession>) => {
    const updatedSessions = sessions.map(s =>
      s.id === sessionId
        ? { ...s, ...updates, updated_at: new Date().toISOString() }
        : s
    )
    saveSessions(updatedSessions)
    if (currentSession?.id === sessionId) {
      setCurrentSession({ ...currentSession, ...updates, updated_at: new Date().toISOString() })
    }
  }

  // Delete session
  const deleteSession = (sessionId: string) => {
    const updatedSessions = sessions.filter(s => s.id !== sessionId)
    saveSessions(updatedSessions)
    if (currentSession?.id === sessionId) {
      setCurrentSession(null)
    }
  }

  // Send message
  const sendMessage = async (content: string, sessionId?: string) => {
    setIsLoading(true)
    setError(null)

    try {
      let session = sessionId ? getSession(sessionId) : currentSession

      // Create new session if none exists
      if (!session) {
        session = createSession()
      }

      // Add user message
      const userMessage: AIChatMessage = {
        id: `msg_${Date.now()}`,
        role: 'user',
        content,
        timestamp: new Date().toISOString(),
      }

      const updatedMessages = [...session.messages, userMessage]
      updateSession(session.id, {
        messages: updatedMessages,
        last_message_preview: content.substring(0, 50),
      })

      // Call AI API
      const request: AIChatRequest = {
        message: content,
        session_id: session.id,
      }

      const response = await apiClient.chatWithAI(request)

      // Add AI response
      const aiMessage: AIChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: response.response,
        timestamp: response.timestamp,
      }

      const finalMessages = [...updatedMessages, aiMessage]
      updateSession(session.id, {
        messages: finalMessages,
        last_message_preview: response.response.substring(0, 50),
      })

      return { success: true, message: aiMessage }
    } catch (err: any) {
      setError(err.message || 'Fehler beim Senden der Nachricht')
      return { success: false, error: err.message }
    } finally {
      setIsLoading(false)
    }
  }

  return {
    sessions,
    currentSession,
    isLoading,
    error,
    createSession,
    getSession,
    updateSession,
    deleteSession,
    sendMessage,
    setCurrentSession,
  }
}
