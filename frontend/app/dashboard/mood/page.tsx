'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import {
  Heart,
  Plus,
  Calendar,
  Zap,
  AlertCircle,
  Moon as MoonIcon,
  TrendingUp,
  Filter,
  Search,
} from 'lucide-react';
import type { MoodEntry, PaginatedResponse } from '@/types';
import { formatDate, formatDateTime, getMoodEmoji, getMoodLabel, getEnergyLabel, getStressLabel } from '@/lib/utils';

export default function MoodListPage() {
  const [moods, setMoods] = useState<MoodEntry[]>([]);
  const [pagination, setPagination] = useState({
    page: 1,
    size: 10,
    total: 0,
    pages: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadMoods();
  }, [pagination.page]);

  const loadMoods = async () => {
    try {
      setIsLoading(true);
      const response: PaginatedResponse<MoodEntry> = await apiClient.getMoodEntries(
        pagination.page,
        pagination.size
      );
      setMoods(response.items);
      setPagination({
        page: response.page,
        size: response.size,
        total: response.total,
        pages: response.pages,
      });
    } catch (error) {
      console.error('Failed to load mood entries:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredMoods = moods.filter((mood) => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      mood.notes?.toLowerCase().includes(searchLower) ||
      mood.activities.some((activity) => activity.toLowerCase().includes(searchLower))
    );
  });

  const getActivityBadge = (activity: string) => {
    const activityMap: { [key: string]: { emoji: string; color: string } } = {
      exercise: { emoji: '🏃', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
      meditation: { emoji: '🧘', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' },
      socializing: { emoji: '👥', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' },
      work: { emoji: '💼', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300' },
      hobbies: { emoji: '🎨', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' },
      reading: { emoji: '📚', color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300' },
      nature: { emoji: '🌳', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
      therapy: { emoji: '💬', color: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300' },
    };

    const activityInfo = activityMap[activity] || { emoji: '✨', color: 'bg-gray-100 text-gray-800' };
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${activityInfo.color}`}>
        {activityInfo.emoji} {activity}
      </span>
    );
  };

  const getAverageMood = () => {
    if (moods.length === 0) return 0;
    const sum = moods.reduce((acc, mood) => acc + mood.mood_score, 0);
    return (sum / moods.length).toFixed(1);
  };

  if (isLoading && moods.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Heart className="h-12 w-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Lade Stimmungseinträge...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Stimmungstagebuch
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Verfolge deine emotionale Reise
          </p>
        </div>
        <Link
          href="/dashboard/mood/new"
          className="inline-flex items-center justify-center bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          <Plus className="h-5 w-5 mr-2" />
          Neue Stimmung
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Gesamt Einträge</p>
              <p className="text-3xl font-bold mt-1">{pagination.total}</p>
            </div>
            <Heart className="h-10 w-10 text-red-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Ø Stimmung</p>
              <p className="text-3xl font-bold mt-1">{getAverageMood()}/10</p>
            </div>
            <TrendingUp className="h-10 w-10 text-green-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Diese Woche</p>
              <p className="text-3xl font-bold mt-1">
                {moods.filter((m) => {
                  const date = new Date(m.created_at);
                  const weekAgo = new Date();
                  weekAgo.setDate(weekAgo.getDate() - 7);
                  return date > weekAgo;
                }).length}
              </p>
            </div>
            <Calendar className="h-10 w-10 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Suche in Notizen oder Aktivitäten..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white"
            />
          </div>
          <button className="inline-flex items-center justify-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors">
            <Filter className="h-5 w-5 mr-2" />
            Filter
          </button>
        </div>
      </div>

      {/* Mood Entries List */}
      {filteredMoods.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-12 shadow text-center">
          <Heart className="h-16 w-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {searchTerm ? 'Keine Einträge gefunden' : 'Noch keine Stimmungseinträge'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {searchTerm
              ? 'Versuche einen anderen Suchbegriff'
              : 'Beginne deine Reise mit deinem ersten Eintrag'}
          </p>
          {!searchTerm && (
            <Link
              href="/dashboard/mood/new"
              className="inline-flex items-center bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              <Plus className="h-5 w-5 mr-2" />
              Ersten Eintrag erstellen
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          {filteredMoods.map((mood) => (
            <Link
              key={mood.id}
              href={`/dashboard/mood/${mood.id}`}
              className="block bg-white dark:bg-gray-800 rounded-lg p-6 shadow hover:shadow-lg transition-shadow border-l-4 border-primary"
            >
              <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
                {/* Left Side - Main Info */}
                <div className="flex-1">
                  <div className="flex items-center space-x-3 mb-3">
                    <span className="text-4xl">{getMoodEmoji(mood.mood_score)}</span>
                    <div>
                      <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                        {getMoodLabel(mood.mood_score)}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {formatDateTime(mood.created_at)}
                      </p>
                    </div>
                  </div>

                  {/* Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                    <div className="flex items-center space-x-2">
                      <Heart className="h-4 w-4 text-red-500" />
                      <span className="text-sm">
                        <span className="font-semibold">{mood.mood_score}</span>/10
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Zap className="h-4 w-4 text-yellow-500" />
                      <span className="text-sm">
                        <span className="font-semibold">{mood.energy_level}</span>/10
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <AlertCircle className="h-4 w-4 text-orange-500" />
                      <span className="text-sm">
                        <span className="font-semibold">{mood.stress_level}</span>/10 Stress
                      </span>
                    </div>
                    <div className="flex items-center space-x-2">
                      <MoonIcon className="h-4 w-4 text-indigo-500" />
                      <span className="text-sm">
                        <span className="font-semibold">{mood.sleep_hours}</span>h Schlaf
                      </span>
                    </div>
                  </div>

                  {/* Activities */}
                  {mood.activities.length > 0 && (
                    <div className="flex flex-wrap gap-2 mb-3">
                      {mood.activities.map((activity) => (
                        <span key={activity}>{getActivityBadge(activity)}</span>
                      ))}
                    </div>
                  )}

                  {/* Notes Preview */}
                  {mood.notes && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                      {mood.notes}
                    </p>
                  )}
                </div>

                {/* Right Side - Visual Score */}
                <div className="flex-shrink-0">
                  <div className="relative w-20 h-20">
                    <svg className="transform -rotate-90 w-20 h-20">
                      <circle
                        cx="40"
                        cy="40"
                        r="36"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        className="text-gray-200 dark:text-gray-700"
                      />
                      <circle
                        cx="40"
                        cy="40"
                        r="36"
                        stroke="currentColor"
                        strokeWidth="8"
                        fill="transparent"
                        strokeDasharray={`${2 * Math.PI * 36}`}
                        strokeDashoffset={`${2 * Math.PI * 36 * (1 - mood.mood_score / 10)}`}
                        className="text-primary"
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-lg font-bold text-primary">{mood.mood_score}</span>
                    </div>
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pagination.pages > 1 && (
        <div className="flex justify-center items-center space-x-2">
          <button
            onClick={() => setPagination({ ...pagination, page: pagination.page - 1 })}
            disabled={pagination.page === 1}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Zurück
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400">
            Seite {pagination.page} von {pagination.pages}
          </span>
          <button
            onClick={() => setPagination({ ...pagination, page: pagination.page + 1 })}
            disabled={pagination.page === pagination.pages}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Weiter
          </button>
        </div>
      )}
    </div>
  );
}
