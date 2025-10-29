'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import {
  ArrowLeft,
  Moon,
  Eye,
  Tag,
  Calendar,
  Clock,
  Sparkles,
  Edit,
  Trash2,
  Loader2,
} from 'lucide-react';
import type { DreamEntry } from '@/types';
import { formatDateTime } from '@/lib/utils';

export default function DreamDetailPage() {
  const router = useRouter();
  const params = useParams();
  const dreamId = params.id as string;

  const [dream, setDream] = useState<DreamEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (dreamId) {
      loadDreamDetail();
    }
  }, [dreamId]);

  const loadDreamDetail = async () => {
    try {
      setIsLoading(true);
      // Note: We need to get single dream - for now using the list endpoint
      const response = await apiClient.getDreamEntries(1, 100);
      const foundDream = response.items.find(d => d.id === dreamId);
      if (foundDream) {
        setDream(foundDream);
      } else {
        router.push('/dashboard/dreams');
      }
    } catch (error) {
      console.error('Failed to load dream entry:', error);
      router.push('/dashboard/dreams');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      setIsDeleting(true);
      // Note: Delete endpoint would need to be added to API client
      // await apiClient.deleteDreamEntry(dreamId);
      router.push('/dashboard/dreams');
    } catch (error) {
      console.error('Failed to delete dream entry:', error);
      alert('Fehler beim Löschen. Bitte versuche es erneut.');
    } finally {
      setIsDeleting(false);
    }
  };

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

    const moodInfo = moodMap[tag] || { emoji: '✨', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', label: tag };
    return (
      <span className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${moodInfo.color}`}>
        <span className="mr-1.5">{moodInfo.emoji}</span>
        {moodInfo.label}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Moon className="h-12 w-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Lade Traum...</p>
        </div>
      </div>
    );
  }

  if (!dream) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
        <div className="flex-1">
          <Link
            href="/dashboard/dreams"
            className="inline-flex items-center text-gray-600 dark:text-gray-400 hover:text-primary mb-3"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Zurück zur Übersicht
          </Link>
          <div className="flex items-start space-x-3 mb-3">
            <Moon className="h-10 w-10 text-indigo-500 flex-shrink-0 mt-1" />
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                {dream.title}
              </h1>
              <div className="flex flex-wrap items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
                <span className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {formatDateTime(dream.created_at)}
                </span>
                {dream.updated_at && dream.updated_at !== dream.created_at && (
                  <span className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    Bearbeitet: {formatDateTime(dream.updated_at)}
                  </span>
                )}
                {dream.lucid && (
                  <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300">
                    <Eye className="h-3 w-3 mr-1" />
                    Luzider Traum
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex space-x-3">
          <Link
            href={`/dashboard/dreams/${dreamId}/edit`}
            className="inline-flex items-center justify-center bg-blue-500 hover:bg-blue-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            <Edit className="h-4 w-4 mr-2" />
            Bearbeiten
          </Link>
          <button
            onClick={() => setShowDeleteConfirm(true)}
            className="inline-flex items-center justify-center bg-red-500 hover:bg-red-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Löschen
          </button>
        </div>
      </div>

      {/* Mood Tag */}
      {dream.mood_tag && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center space-x-2 mb-3">
            <Tag className="h-5 w-5 text-purple-500" />
            <h2 className="text-lg font-semibold">Stimmung</h2>
          </div>
          {getMoodTagBadge(dream.mood_tag)}
        </div>
      )}

      {/* Dream Content */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
        <h2 className="text-xl font-bold mb-4">Traumbeschreibung</h2>
        <div className="prose dark:prose-invert max-w-none">
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
            {dream.content}
          </p>
        </div>
      </div>

      {/* AI Interpretation */}
      {dream.interpretation && (
        <div className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg p-6 shadow border border-indigo-200 dark:border-indigo-800">
          <div className="flex items-center space-x-2 mb-4">
            <Sparkles className="h-6 w-6 text-indigo-600 dark:text-indigo-400" />
            <h2 className="text-xl font-bold text-indigo-900 dark:text-indigo-100">
              KI-Interpretation
            </h2>
          </div>
          <div className="bg-white/50 dark:bg-gray-800/50 rounded-lg p-4">
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
              {dream.interpretation}
            </p>
          </div>
        </div>
      )}

      {/* Dream Insights Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
        <h2 className="text-xl font-bold mb-4">Traum-Insights</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Moon className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              <span className="text-sm font-medium text-indigo-900 dark:text-indigo-100">
                Traumtyp
              </span>
            </div>
            <p className="text-lg font-bold text-indigo-900 dark:text-indigo-100">
              {dream.lucid ? 'Luzider Traum' : 'Normaler Traum'}
            </p>
          </div>

          <div className="bg-purple-50 dark:bg-purple-900/20 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Tag className="h-5 w-5 text-purple-600 dark:text-purple-400" />
              <span className="text-sm font-medium text-purple-900 dark:text-purple-100">
                Länge
              </span>
            </div>
            <p className="text-lg font-bold text-purple-900 dark:text-purple-100">
              {dream.content.length} Zeichen
            </p>
          </div>

          <div className="bg-pink-50 dark:bg-pink-900/20 rounded-lg p-4">
            <div className="flex items-center space-x-2 mb-2">
              <Sparkles className="h-5 w-5 text-pink-600 dark:text-pink-400" />
              <span className="text-sm font-medium text-pink-900 dark:text-pink-100">
                KI-Analyse
              </span>
            </div>
            <p className="text-lg font-bold text-pink-900 dark:text-pink-100">
              {dream.interpretation ? 'Vorhanden' : 'Nicht vorhanden'}
            </p>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full shadow-xl">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Traum löschen?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Möchtest du diesen Traum wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.
            </p>
            <div className="flex space-x-3">
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="flex-1 bg-red-500 hover:bg-red-600 text-white font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
              >
                {isDeleting ? (
                  <>
                    <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
                    Löschen...
                  </>
                ) : (
                  'Ja, löschen'
                )}
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                disabled={isDeleting}
                className="flex-1 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white font-semibold py-3 px-4 rounded-lg transition-colors"
              >
                Abbrechen
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
