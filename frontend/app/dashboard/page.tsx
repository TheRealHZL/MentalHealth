'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/hooks/useAuth';
import { apiClient } from '@/lib/api';
import {
  Heart,
  Moon,
  Plus,
  TrendingUp,
  Activity,
  Calendar,
  Brain,
  Sparkles,
} from 'lucide-react';
import type { OverviewStats, WellnessScore, MoodEntry } from '@/types';
import { formatDate, getMoodEmoji } from '@/lib/utils';

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<OverviewStats | null>(null);
  const [wellnessScore, setWellnessScore] = useState<WellnessScore | null>(null);
  const [recentMoods, setRecentMoods] = useState<MoodEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const [statsData, wellnessData, moodsData] = await Promise.all([
        apiClient.getOverviewStats(),
        apiClient.getWellnessScore(),
        apiClient.getMoodEntries(1, 5),
      ]);

      setStats(statsData);
      setWellnessScore(wellnessData);
      setRecentMoods(moodsData.items);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getWellnessScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 dark:text-green-400';
    if (score >= 60) return 'text-blue-600 dark:text-blue-400';
    if (score >= 40) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getTrendIcon = (trend: string) => {
    if (trend === 'improving') return '📈';
    if (trend === 'declining') return '📉';
    return '➡️';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Brain className="h-12 w-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Lade Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-lg p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">
          Willkommen zurück, {user?.first_name}! 👋
        </h1>
        <p className="text-blue-100">
          Schön, dass du da bist. Wie geht es dir heute?
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link
          href="/dashboard/mood/new"
          className="bg-white dark:bg-gray-800 rounded-lg p-6 border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-primary dark:hover:border-primary transition-colors group"
        >
          <div className="flex items-center space-x-4">
            <div className="bg-primary/10 group-hover:bg-primary group-hover:text-white p-3 rounded-lg transition-colors">
              <Plus className="h-6 w-6 text-primary group-hover:text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Neue Stimmung erfassen</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Wie fühlst du dich gerade?
              </p>
            </div>
          </div>
        </Link>

        <Link
          href="/dashboard/dreams/new"
          className="bg-white dark:bg-gray-800 rounded-lg p-6 border-2 border-dashed border-gray-300 dark:border-gray-600 hover:border-primary dark:hover:border-primary transition-colors group"
        >
          <div className="flex items-center space-x-4">
            <div className="bg-primary/10 group-hover:bg-primary group-hover:text-white p-3 rounded-lg transition-colors">
              <Plus className="h-6 w-6 text-primary group-hover:text-white" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">Neuen Traum eintragen</h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Erinnere dich an deinen letzten Traum
              </p>
            </div>
          </div>
        </Link>
      </div>

      {/* Wellness Score Card */}
      {wellnessScore && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold flex items-center space-x-2">
              <Sparkles className="h-6 w-6 text-primary" />
              <span>Dein Wellness-Score</span>
            </h2>
            <span className="text-2xl">{getTrendIcon(wellnessScore.trend)}</span>
          </div>

          <div className="flex items-center space-x-6">
            <div className="flex-shrink-0">
              <div className="relative w-32 h-32">
                <svg className="transform -rotate-90 w-32 h-32">
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    className="text-gray-200 dark:text-gray-700"
                  />
                  <circle
                    cx="64"
                    cy="64"
                    r="56"
                    stroke="currentColor"
                    strokeWidth="8"
                    fill="transparent"
                    strokeDasharray={`${2 * Math.PI * 56}`}
                    strokeDashoffset={`${2 * Math.PI * 56 * (1 - wellnessScore.score / 100)}`}
                    className={getWellnessScoreColor(wellnessScore.score)}
                    strokeLinecap="round"
                  />
                </svg>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className={`text-3xl font-bold ${getWellnessScoreColor(wellnessScore.score)}`}>
                    {wellnessScore.score}
                  </span>
                </div>
              </div>
            </div>

            <div className="flex-1 grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Stimmung</p>
                <p className="text-2xl font-bold">{wellnessScore.factors.mood}/10</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Energie</p>
                <p className="text-2xl font-bold">{wellnessScore.factors.energy}/10</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Schlaf</p>
                <p className="text-2xl font-bold">{wellnessScore.factors.sleep}/10</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Stress</p>
                <p className="text-2xl font-bold">{10 - wellnessScore.factors.stress}/10</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Stats Grid */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Stimmungseinträge</p>
                <p className="text-3xl font-bold mt-1">{stats.total_mood_entries}</p>
              </div>
              <Heart className="h-10 w-10 text-red-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Traumeinträge</p>
                <p className="text-3xl font-bold mt-1">{stats.total_dream_entries}</p>
              </div>
              <Moon className="h-10 w-10 text-indigo-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Ø Stimmung</p>
                <p className="text-3xl font-bold mt-1">{stats.average_mood.toFixed(1)}</p>
              </div>
              <Activity className="h-10 w-10 text-green-500" />
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Ø Schlaf</p>
                <p className="text-3xl font-bold mt-1">{stats.average_sleep_hours.toFixed(1)}h</p>
              </div>
              <Calendar className="h-10 w-10 text-blue-500" />
            </div>
          </div>
        </div>
      )}

      {/* Recent Mood Entries */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Letzte Stimmungseinträge</h2>
          <Link
            href="/dashboard/mood"
            className="text-primary hover:underline text-sm font-medium"
          >
            Alle ansehen →
          </Link>
        </div>

        {recentMoods.length === 0 ? (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Heart className="h-12 w-12 mx-auto mb-2 opacity-50" />
            <p>Noch keine Stimmungseinträge vorhanden.</p>
            <Link
              href="/dashboard/mood/new"
              className="text-primary hover:underline mt-2 inline-block"
            >
              Erstelle deinen ersten Eintrag
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {recentMoods.map((mood) => (
              <Link
                key={mood.id}
                href={`/dashboard/mood/${mood.id}`}
                className="flex items-center justify-between p-4 rounded-lg border border-gray-200 dark:border-gray-700 hover:border-primary dark:hover:border-primary transition-colors"
              >
                <div className="flex items-center space-x-4">
                  <span className="text-3xl">{getMoodEmoji(mood.mood_score)}</span>
                  <div>
                    <p className="font-medium">
                      Stimmung: {mood.mood_score}/10
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {formatDate(mood.created_at)}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Energie: {mood.energy_level}/10
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    Stress: {mood.stress_level}/10
                  </p>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
