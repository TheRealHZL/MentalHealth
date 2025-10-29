'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import {
  Moon,
  Plus,
  Calendar,
  Eye,
  Sparkles,
  Search,
  Filter,
  Tag,
} from 'lucide-react';
import type { DreamEntry, PaginatedResponse } from '@/types';
import { formatDate, formatDateTime } from '@/lib/utils';

export default function DreamsListPage() {
  const [dreams, setDreams] = useState<DreamEntry[]>([]);
  const [pagination, setPagination] = useState({
    page: 1,
    size: 10,
    total: 0,
    pages: 0,
  });
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadDreams();
  }, [pagination.page]);

  const loadDreams = async () => {
    try {
      setIsLoading(true);
      const response: PaginatedResponse<DreamEntry> = await apiClient.getDreamEntries(
        pagination.page,
        pagination.size
      );
      setDreams(response.items);
      setPagination({
        page: response.page,
        size: response.size,
        total: response.total,
        pages: response.pages,
      });
    } catch (error) {
      console.error('Failed to load dream entries:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const filteredDreams = dreams.filter((dream) => {
    if (!searchTerm) return true;
    const searchLower = searchTerm.toLowerCase();
    return (
      dream.title.toLowerCase().includes(searchLower) ||
      dream.content.toLowerCase().includes(searchLower) ||
      dream.mood_tag?.toLowerCase().includes(searchLower)
    );
  });

  const getMoodTagBadge = (tag: string) => {
    const moodMap: { [key: string]: { emoji: string; color: string; label: string } } = {
      happy: { emoji: '😊', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300', label: 'Fröhlich' },
      anxious: { emoji: '😰', color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300', label: 'Ängstlich' },
      sad: { emoji: '😢', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300', label: 'Traurig' },
      peaceful: { emoji: '😌', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300', label: 'Friedlich' },
      exciting: { emoji: '🤩', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300', label: 'Aufregend' },
      confused: { emoji: '😕', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', label: 'Verwirrt' },
      scary: { emoji: '😱', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300', label: 'Beängstigend' },
      romantic: { emoji: '😍', color: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300', label: 'Romantisch' },
    };

    const moodInfo = moodMap[tag] || { emoji: '✨', color: 'bg-gray-100 text-gray-800', label: tag };
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${moodInfo.color}`}>
        {moodInfo.emoji} {moodInfo.label}
      </span>
    );
  };

  const getLucidDreamCount = () => {
    return dreams.filter((d) => d.lucid).length;
  };

  if (isLoading && dreams.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Moon className="h-12 w-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Lade Traumtagebuch...</p>
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
            Traumtagebuch
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Erkunde deine nächtlichen Abenteuer
          </p>
        </div>
        <Link
          href="/dashboard/dreams/new"
          className="inline-flex items-center justify-center bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 px-6 rounded-lg transition-colors"
        >
          <Plus className="h-5 w-5 mr-2" />
          Neuer Traum
        </Link>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Gesamt Träume</p>
              <p className="text-3xl font-bold mt-1">{pagination.total}</p>
            </div>
            <Moon className="h-10 w-10 text-indigo-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Luzide Träume</p>
              <p className="text-3xl font-bold mt-1">{getLucidDreamCount()}</p>
            </div>
            <Eye className="h-10 w-10 text-purple-500" />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Diese Woche</p>
              <p className="text-3xl font-bold mt-1">
                {dreams.filter((d) => {
                  const date = new Date(d.created_at);
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
              placeholder="Suche in Titel, Beschreibung oder Tags..."
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

      {/* Dreams List */}
      {filteredDreams.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-12 shadow text-center">
          <Moon className="h-16 w-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            {searchTerm ? 'Keine Träume gefunden' : 'Noch keine Träume eingetragen'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            {searchTerm
              ? 'Versuche einen anderen Suchbegriff'
              : 'Beginne dein Traumtagebuch mit deinem ersten Eintrag'}
          </p>
          {!searchTerm && (
            <Link
              href="/dashboard/dreams/new"
              className="inline-flex items-center bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 px-6 rounded-lg transition-colors"
            >
              <Plus className="h-5 w-5 mr-2" />
              Ersten Traum eintragen
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredDreams.map((dream) => (
            <Link
              key={dream.id}
              href={`/dashboard/dreams/${dream.id}`}
              className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow hover:shadow-lg transition-shadow border-l-4 border-indigo-500"
            >
              {/* Header */}
              <div className="flex items-start justify-between mb-3">
                <div className="flex-1">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-1">
                    {dream.title}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {formatDateTime(dream.created_at)}
                  </p>
                </div>
                {dream.lucid && (
                  <div className="flex-shrink-0 ml-2">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300">
                      <Eye className="h-3 w-3 mr-1" />
                      Luzid
                    </span>
                  </div>
                )}
              </div>

              {/* Content Preview */}
              <p className="text-gray-600 dark:text-gray-400 line-clamp-3 mb-4">
                {dream.content}
              </p>

              {/* Footer */}
              <div className="flex items-center justify-between">
                {/* Mood Tag */}
                {dream.mood_tag && (
                  <div>{getMoodTagBadge(dream.mood_tag)}</div>
                )}

                {/* Interpretation Badge */}
                {dream.interpretation && (
                  <div className="flex items-center text-xs text-indigo-600 dark:text-indigo-400">
                    <Sparkles className="h-3 w-3 mr-1" />
                    KI-Interpretation verfügbar
                  </div>
                )}
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
