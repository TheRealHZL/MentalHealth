'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Heart, Moon, FileText, Calendar, MessageSquare, Zap } from 'lucide-react'
import Link from 'next/link'

interface QuickAction {
  title: string
  description: string
  icon: React.ReactNode
  href: string
  color: string
}

const quickActions: QuickAction[] = [
  {
    title: 'Stimmung erfassen',
    description: 'Aktuellen Zustand festhalten',
    icon: <Heart className="h-5 w-5" />,
    href: '/dashboard/mood/new',
    color: 'bg-red-500/10 text-red-600 dark:text-red-400',
  },
  {
    title: 'Traum aufzeichnen',
    description: 'Neuen Traum dokumentieren',
    icon: <Moon className="h-5 w-5" />,
    href: '/dashboard/dreams/new',
    color: 'bg-purple-500/10 text-purple-600 dark:text-purple-400',
  },
  {
    title: 'Therapienotiz',
    description: 'Neue Notiz erstellen',
    icon: <FileText className="h-5 w-5" />,
    href: '/dashboard/therapy/notes/new',
    color: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  },
  {
    title: 'AI Chat',
    description: 'Mit Assistent sprechen',
    icon: <MessageSquare className="h-5 w-5" />,
    href: '/dashboard/chat',
    color: 'bg-green-500/10 text-green-600 dark:text-green-400',
  },
]

export function QuickActionsWidget() {
  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Schnellzugriff
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {quickActions.map((action) => (
            <Link
              key={action.href}
              href={action.href}
              className="flex items-start gap-3 p-4 rounded-lg border border-border hover:bg-muted/50 transition-all hover:scale-105 active:scale-95"
            >
              <div className={`p-2 rounded-lg ${action.color}`}>
                {action.icon}
              </div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-sm">{action.title}</div>
                <p className="text-xs text-muted-foreground mt-0.5 truncate">
                  {action.description}
                </p>
              </div>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
