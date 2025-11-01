'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'
import { Users, Key, LayoutDashboard, LogOut } from 'lucide-react'

export default function TherapistLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const { user, isAuthenticated, isLoading, logout } = useAuth()

  useEffect(() => {
    if (!isLoading) {
      // Redirect if not authenticated
      if (!isAuthenticated) {
        router.push('/login')
      } else if (user?.role !== 'therapist') {
        // Redirect if not therapist
        router.push('/dashboard')
      }
    }
  }, [isLoading, isAuthenticated, user, router])

  const handleLogout = () => {
    logout()
    router.push('/login')
  }

  if (isLoading || !isAuthenticated || user?.role !== 'therapist') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <aside className="fixed left-0 top-0 h-full w-64 bg-white dark:bg-gray-800 shadow-lg z-10">
        <div className="p-6">
          <h1 className="text-2xl font-bold text-primary">MindBridge</h1>
          <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Therapeuten-Portal</p>
        </div>

        <nav className="px-4 space-y-2">
          <Link
            href="/therapist"
            className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <LayoutDashboard className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <span className="text-gray-700 dark:text-gray-300">Dashboard</span>
          </Link>

          <Link
            href="/therapist/patients"
            className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <Users className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <span className="text-gray-700 dark:text-gray-300">Meine Patienten</span>
          </Link>

          <Link
            href="/therapist/share-keys"
            className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <Key className="h-5 w-5 text-gray-600 dark:text-gray-400" />
            <span className="text-gray-700 dark:text-gray-300">Zugriffsverwaltung</span>
          </Link>
        </nav>

        <div className="absolute bottom-0 w-full p-4 border-t border-gray-200 dark:border-gray-700">
          <div className="mb-4 px-4">
            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
              {user.first_name} {user.last_name}
            </p>
            <p className="text-xs text-gray-500 dark:text-gray-400">{user.email}</p>
          </div>
          <button
            onClick={handleLogout}
            className="flex items-center space-x-2 w-full px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
          >
            <LogOut className="h-4 w-4" />
            <span>Abmelden</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="ml-64 p-8">
        {children}
      </main>
    </div>
  )
}
