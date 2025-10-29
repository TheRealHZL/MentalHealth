'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { apiClient } from '@/lib/api';
import {
  ArrowLeft,
  Heart,
  Zap,
  AlertCircle,
  Moon as MoonIcon,
  Star,
  Edit,
  Trash2,
  Calendar,
  Clock,
  Loader2,
} from 'lucide-react';
import type { MoodEntry } from '@/types';
import { formatDateTime, getMoodEmoji, getMoodLabel, getEnergyLabel, getStressLabel, getSleepQualityLabel } from '@/lib/utils';

export default function MoodDetailPage() {
  const router = useRouter();
  const params = useParams();
  const moodId = params.id as string;

  const [mood, setMood] = useState<MoodEntry | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  useEffect(() => {
    if (moodId) {
      loadMoodDetail();
    }
  }, [moodId]);

  const loadMoodDetail = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getMoodEntry(moodId);
      setMood(data);
    } catch (error) {
      console.error('Failed to load mood entry:', error);
      router.push('/dashboard/mood');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async () => {
    try {
      setIsDeleting(true);
      await apiClient.deleteMoodEntry(moodId);
      router.push('/dashboard/mood');
    } catch (error) {
      console.error('Failed to delete mood entry:', error);
      alert('Fehler beim Löschen. Bitte versuche es erneut.');
    } finally {
      setIsDeleting(false);
    }
  };

  const getActivityBadge = (activity: string) => {
    const activityMap: { [key: string]: { emoji: string; color: string; label: string } } = {
      exercise: { emoji: '🏃', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300', label: 'Sport' },
      meditation: { emoji: '🧘', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300', label: 'Meditation' },
      socializing: { emoji: '👥', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300', label: 'Soziale Aktivitäten' },
      work: { emoji: '💼', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', label: 'Arbeit' },
      hobbies: { emoji: '🎨', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300', label: 'Hobbys' },
      reading: { emoji: '📚', color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300', label: 'Lesen' },
      nature: { emoji: '🌳', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300', label: 'Natur' },
      therapy: { emoji: '💬', color: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300', label: 'Therapie' },
    };

    const activityInfo = activityMap[activity] || { emoji: '✨', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300', label: activity };
    return (
      <span key={activity} className={`inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium ${activityInfo.color}`}>
        <span className="mr-1.5">{activityInfo.emoji}</span>
        {activityInfo.label}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <Heart className="h-12 w-12 text-primary animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Lade Eintrag...</p>
        </div>
      </div>
    );
  }

  if (!mood) {
    return null;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <Link
            href="/dashboard/mood"
            className="inline-flex items-center text-gray-600 dark:text-gray-400 hover:text-primary mb-3"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Zurück zur Übersicht
          </Link>
          <div className="flex items-center space-x-3">
            <span className="text-5xl">{getMoodEmoji(mood.mood_score)}</span>
            <div>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                {getMoodLabel(mood.mood_score)}
              </h1>
              <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400 mt-1">
                <span className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  {formatDateTime(mood.created_at)}
                </span>
                {mood.updated_at && mood.updated_at !== mood.created_at && (
                  <span className="flex items-center">
                    <Clock className="h-4 w-4 mr-1" />
                    Bearbeitet: {formatDateTime(mood.updated_at)}
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>

        <div className="flex space-x-3">
          <Link
            href={`/dashboard/mood/${moodId}/edit`}
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

      {/* Main Scores Card */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-lg">
        <h2 className="text-xl font-bold mb-6">Bewertungen</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Mood Score */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Heart className="h-5 w-5 text-red-500" />
                <span className="font-semibold">Stimmung</span>
              </div>
              <span className="text-2xl font-bold text-red-500">{mood.mood_score}/10</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                className="bg-red-500 h-3 rounded-full transition-all"
                style={{ width: `${(mood.mood_score / 10) * 100}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">{getMoodLabel(mood.mood_score)}</p>
          </div>

          {/* Energy Level */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Zap className="h-5 w-5 text-yellow-500" />
                <span className="font-semibold">Energie</span>
              </div>
              <span className="text-2xl font-bold text-yellow-500">{mood.energy_level}/10</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                className="bg-yellow-500 h-3 rounded-full transition-all"
                style={{ width: `${(mood.energy_level / 10) * 100}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">{getEnergyLabel(mood.energy_level)}</p>
          </div>

          {/* Stress Level */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-5 w-5 text-orange-500" />
                <span className="font-semibold">Stress</span>
              </div>
              <span className="text-2xl font-bold text-orange-500">{mood.stress_level}/10</span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
              <div
                className="bg-orange-500 h-3 rounded-full transition-all"
                style={{ width: `${(mood.stress_level / 10) * 100}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">{getStressLabel(mood.stress_level)}</p>
          </div>

          {/* Sleep */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <MoonIcon className="h-5 w-5 text-indigo-500" />
                <span className="font-semibold">Schlaf</span>
              </div>
              <span className="text-2xl font-bold text-indigo-500">{mood.sleep_hours}h</span>
            </div>
            <div className="flex items-center space-x-1">
              {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
                <Star
                  key={rating}
                  className={`h-4 w-4 ${
                    rating <= mood.sleep_quality
                      ? 'text-yellow-400 fill-yellow-400'
                      : 'text-gray-300 dark:text-gray-600'
                  }`}
                />
              ))}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              Qualität: {getSleepQualityLabel(mood.sleep_quality)}
            </p>
          </div>
        </div>
      </div>

      {/* Activities Card */}
      {mood.activities.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <h2 className="text-xl font-bold mb-4">Aktivitäten</h2>
          <div className="flex flex-wrap gap-2">
            {mood.activities.map((activity) => getActivityBadge(activity))}
          </div>
        </div>
      )}

      {/* Notes Card */}
      {mood.notes && (
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <h2 className="text-xl font-bold mb-4">Notizen</h2>
          <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
            {mood.notes}
          </p>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full shadow-xl">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
              Eintrag löschen?
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-6">
              Möchtest du diesen Stimmungseintrag wirklich löschen? Diese Aktion kann nicht rückgängig gemacht werden.
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
