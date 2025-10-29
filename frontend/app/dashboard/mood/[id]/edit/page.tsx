'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { apiClient } from '@/lib/api';
import {
  ArrowLeft,
  Heart,
  Zap,
  AlertCircle,
  Moon as MoonIcon,
  Star,
  Loader2,
  Sparkles,
  Save,
} from 'lucide-react';
import Link from 'next/link';
import type { MoodEntry, CreateMoodRequest } from '@/types';

const moodSchema = z.object({
  mood_score: z.number().min(1).max(10),
  energy_level: z.number().min(1).max(10),
  stress_level: z.number().min(1).max(10),
  sleep_hours: z.number().min(0).max(24),
  sleep_quality: z.number().min(1).max(10),
  activities: z.array(z.string()),
  notes: z.string().optional(),
});

type MoodFormData = z.infer<typeof moodSchema>;

const activityOptions = [
  { value: 'exercise', label: '🏃 Sport', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
  { value: 'meditation', label: '🧘 Meditation', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' },
  { value: 'socializing', label: '👥 Soziale Aktivitäten', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' },
  { value: 'work', label: '💼 Arbeit', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300' },
  { value: 'hobbies', label: '🎨 Hobbys', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' },
  { value: 'reading', label: '📚 Lesen', color: 'bg-indigo-100 text-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300' },
  { value: 'nature', label: '🌳 Natur', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
  { value: 'therapy', label: '💬 Therapie', color: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300' },
];

export default function EditMoodPage() {
  const router = useRouter();
  const params = useParams();
  const moodId = params.id as string;

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string>('');
  const [mood, setMood] = useState<MoodEntry | null>(null);

  const {
    register,
    handleSubmit,
    control,
    watch,
    reset,
    formState: { errors },
  } = useForm<MoodFormData>({
    resolver: zodResolver(moodSchema),
  });

  const watchedActivities = watch('activities');
  const watchedMoodScore = watch('mood_score');

  useEffect(() => {
    if (moodId) {
      loadMoodEntry();
    }
  }, [moodId]);

  const loadMoodEntry = async () => {
    try {
      setIsLoading(true);
      const data = await apiClient.getMoodEntry(moodId);
      setMood(data);
      
      // Populate form with existing data
      reset({
        mood_score: data.mood_score,
        energy_level: data.energy_level,
        stress_level: data.stress_level,
        sleep_hours: data.sleep_hours,
        sleep_quality: data.sleep_quality,
        activities: data.activities,
        notes: data.notes || '',
      });
    } catch (error) {
      console.error('Failed to load mood entry:', error);
      router.push('/dashboard/mood');
    } finally {
      setIsLoading(false);
    }
  };

  const toggleActivity = (activity: string, currentActivities: string[]) => {
    if (currentActivities.includes(activity)) {
      return currentActivities.filter((a) => a !== activity);
    }
    return [...currentActivities, activity];
  };

  const onSubmit = async (data: MoodFormData) => {
    try {
      setIsSaving(true);
      setError('');

      await apiClient.updateMoodEntry(moodId, data);
      router.push(`/dashboard/mood/${moodId}`);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          'Fehler beim Speichern. Bitte versuche es erneut.'
      );
    } finally {
      setIsSaving(false);
    }
  };

  const getMoodEmoji = (score: number) => {
    if (score >= 9) return '😊';
    if (score >= 7) return '🙂';
    if (score >= 5) return '😐';
    if (score >= 3) return '😕';
    return '😢';
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
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          href={`/dashboard/mood/${moodId}`}
          className="inline-flex items-center text-gray-600 dark:text-gray-400 hover:text-primary mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Zurück zum Eintrag
        </Link>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Eintrag bearbeiten {getMoodEmoji(watchedMoodScore || mood.mood_score)}
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-2">
          Aktualisiere deine Stimmungsdaten
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Mood Score */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center space-x-2 mb-4">
            <Heart className="h-5 w-5 text-red-500" />
            <label className="text-lg font-semibold">Stimmung</label>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Wie würdest du deine Stimmung bewerten?
          </p>
          <Controller
            name="mood_score"
            control={control}
            render={({ field }) => (
              <div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  {...field}
                  onChange={(e) => field.onChange(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-red-500"
                />
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mt-2">
                  <span>Sehr schlecht</span>
                  <span className="text-2xl font-bold text-red-500">{field.value}/10</span>
                  <span>Ausgezeichnet</span>
                </div>
              </div>
            )}
          />
          {errors.mood_score && (
            <p className="mt-2 text-sm text-red-600">{errors.mood_score.message}</p>
          )}
        </div>

        {/* Energy Level */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center space-x-2 mb-4">
            <Zap className="h-5 w-5 text-yellow-500" />
            <label className="text-lg font-semibold">Energie-Level</label>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Wie energiegeladen fühlst du dich?
          </p>
          <Controller
            name="energy_level"
            control={control}
            render={({ field }) => (
              <div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  {...field}
                  onChange={(e) => field.onChange(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-yellow-500"
                />
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mt-2">
                  <span>Erschöpft</span>
                  <span className="text-2xl font-bold text-yellow-500">{field.value}/10</span>
                  <span>Sehr energiegeladen</span>
                </div>
              </div>
            )}
          />
        </div>

        {/* Stress Level */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center space-x-2 mb-4">
            <AlertCircle className="h-5 w-5 text-orange-500" />
            <label className="text-lg font-semibold">Stress-Level</label>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Wie gestresst fühlst du dich?
          </p>
          <Controller
            name="stress_level"
            control={control}
            render={({ field }) => (
              <div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  {...field}
                  onChange={(e) => field.onChange(Number(e.target.value))}
                  className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer accent-orange-500"
                />
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400 mt-2">
                  <span>Entspannt</span>
                  <span className="text-2xl font-bold text-orange-500">{field.value}/10</span>
                  <span>Sehr gestresst</span>
                </div>
              </div>
            )}
          />
        </div>

        {/* Sleep */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center space-x-2 mb-4">
            <MoonIcon className="h-5 w-5 text-indigo-500" />
            <label className="text-lg font-semibold">Schlaf</label>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Sleep Hours */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Schlafdauer (Stunden)
              </label>
              <input
                {...register('sleep_hours', { valueAsNumber: true })}
                type="number"
                step="0.5"
                min="0"
                max="24"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
              {errors.sleep_hours && (
                <p className="mt-1 text-sm text-red-600">{errors.sleep_hours.message}</p>
              )}
            </div>

            {/* Sleep Quality */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Schlafqualität
              </label>
              <Controller
                name="sleep_quality"
                control={control}
                render={({ field }) => (
                  <div className="flex items-center space-x-2">
                    {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((rating) => (
                      <button
                        key={rating}
                        type="button"
                        onClick={() => field.onChange(rating)}
                        className="focus:outline-none"
                      >
                        <Star
                          className={`h-6 w-6 ${
                            rating <= field.value
                              ? 'text-yellow-400 fill-yellow-400'
                              : 'text-gray-300 dark:text-gray-600'
                          }`}
                        />
                      </button>
                    ))}
                  </div>
                )}
              />
            </div>
          </div>
        </div>

        {/* Activities */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center space-x-2 mb-4">
            <Sparkles className="h-5 w-5 text-purple-500" />
            <label className="text-lg font-semibold">Aktivitäten</label>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Was hast du gemacht?
          </p>
          <Controller
            name="activities"
            control={control}
            render={({ field }) => (
              <div className="flex flex-wrap gap-2">
                {activityOptions.map((activity) => (
                  <button
                    key={activity.value}
                    type="button"
                    onClick={() =>
                      field.onChange(toggleActivity(activity.value, field.value || []))
                    }
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      field.value?.includes(activity.value)
                        ? activity.color + ' ring-2 ring-offset-2 ring-primary dark:ring-offset-gray-800'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {activity.label}
                  </button>
                ))}
              </div>
            )}
          />
        </div>

        {/* Notes */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <label className="text-lg font-semibold mb-4 block">
            Notizen (optional)
          </label>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Möchtest du noch etwas hinzufügen?
          </p>
          <textarea
            {...register('notes')}
            rows={4}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white"
            placeholder="Schreibe hier deine Gedanken..."
          />
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-600 dark:text-red-400 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Submit Buttons */}
        <div className="flex space-x-4">
          <button
            type="submit"
            disabled={isSaving}
            className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isSaving ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
                Speichern...
              </>
            ) : (
              <>
                <Save className="h-5 w-5 mr-2" />
                Änderungen speichern
              </>
            )}
          </button>
          <Link
            href={`/dashboard/mood/${moodId}`}
            className="px-6 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg font-semibold hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-center"
          >
            Abbrechen
          </Link>
        </div>
      </form>
    </div>
  );
}
