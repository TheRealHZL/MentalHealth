'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { apiClient } from '@/lib/api';
import {
  ArrowLeft,
  Moon,
  Sparkles,
  Loader2,
  Eye,
  Tag,
} from 'lucide-react';
import Link from 'next/link';
import type { CreateDreamRequest } from '@/types';

const dreamSchema = z.object({
  title: z.string().min(3, 'Titel muss mindestens 3 Zeichen lang sein'),
  content: z.string().min(10, 'Beschreibung muss mindestens 10 Zeichen lang sein'),
  mood_tag: z.string().optional(),
  lucid: z.boolean(),
});

type DreamFormData = z.infer<typeof dreamSchema>;

const moodTags = [
  { value: 'happy', label: '😊 Fröhlich', color: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300' },
  { value: 'anxious', label: '😰 Ängstlich', color: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300' },
  { value: 'sad', label: '😢 Traurig', color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300' },
  { value: 'peaceful', label: '😌 Friedlich', color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300' },
  { value: 'exciting', label: '🤩 Aufregend', color: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300' },
  { value: 'confused', label: '😕 Verwirrt', color: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300' },
  { value: 'scary', label: '😱 Beängstigend', color: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300' },
  { value: 'romantic', label: '😍 Romantisch', color: 'bg-pink-100 text-pink-800 dark:bg-pink-900/30 dark:text-pink-300' },
];

export default function NewDreamPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [isInterpreting, setIsInterpreting] = useState(false);
  const [error, setError] = useState<string>('');
  const [interpretation, setInterpretation] = useState<string>('');

  const {
    register,
    handleSubmit,
    control,
    watch,
    formState: { errors },
  } = useForm<DreamFormData>({
    resolver: zodResolver(dreamSchema),
    defaultValues: {
      title: '',
      content: '',
      mood_tag: '',
      lucid: false,
    },
  });

  const watchedContent = watch('content');
  const watchedMoodTag = watch('mood_tag');
  const watchedLucid = watch('lucid');

  const onSubmit = async (data: DreamFormData) => {
    try {
      setIsLoading(true);
      setError('');

      await apiClient.createDreamEntry(data);
      router.push('/dashboard/dreams');
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          'Fehler beim Speichern. Bitte versuche es erneut.'
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleInterpret = async () => {
    if (!watchedContent || watchedContent.length < 10) {
      setError('Bitte beschreibe deinen Traum ausführlicher, bevor du ihn interpretieren lässt.');
      return;
    }

    try {
      setIsInterpreting(true);
      setError('');
      const result = await apiClient.interpretDream({ dream_text: watchedContent });
      setInterpretation(result.interpretation);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          'Fehler bei der Interpretation. Bitte versuche es erneut.'
      );
    } finally {
      setIsInterpreting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <Link
          href="/dashboard/dreams"
          className="inline-flex items-center text-gray-600 dark:text-gray-400 hover:text-primary mb-4"
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Zurück zur Übersicht
        </Link>
        <div className="flex items-center space-x-3">
          <Moon className="h-10 w-10 text-indigo-500" />
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
              Neuen Traum eintragen
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-1">
              Halte deinen Traum fest, solange du dich noch erinnerst
            </p>
          </div>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Title */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <label
            htmlFor="title"
            className="block text-lg font-semibold mb-2"
          >
            Titel *
          </label>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Gib deinem Traum einen beschreibenden Titel
          </p>
          <input
            {...register('title')}
            type="text"
            id="title"
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white text-lg"
            placeholder="z.B. Der Flug über die Stadt"
          />
          {errors.title && (
            <p className="mt-2 text-sm text-red-600">{errors.title.message}</p>
          )}
        </div>

        {/* Content */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <label
            htmlFor="content"
            className="block text-lg font-semibold mb-2"
          >
            Traumbeschreibung *
          </label>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Beschreibe deinen Traum so detailliert wie möglich
          </p>
          <textarea
            {...register('content')}
            id="content"
            rows={8}
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent dark:bg-gray-700 dark:text-white"
            placeholder="Ich träumte, dass ich durch eine große Stadt flog. Die Gebäude waren golden und..."
          />
          {errors.content && (
            <p className="mt-2 text-sm text-red-600">{errors.content.message}</p>
          )}
          <div className="mt-2 flex items-center justify-between">
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {watchedContent?.length || 0} Zeichen
            </p>
            <button
              type="button"
              onClick={handleInterpret}
              disabled={isInterpreting || !watchedContent || watchedContent.length < 10}
              className="inline-flex items-center px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium"
            >
              {isInterpreting ? (
                <>
                  <Loader2 className="animate-spin h-4 w-4 mr-2" />
                  Interpretiere...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  KI-Interpretation
                </>
              )}
            </button>
          </div>
        </div>

        {/* AI Interpretation Result */}
        {interpretation && (
          <div className="bg-gradient-to-br from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 rounded-lg p-6 border border-indigo-200 dark:border-indigo-800">
            <div className="flex items-center space-x-2 mb-3">
              <Sparkles className="h-5 w-5 text-indigo-600 dark:text-indigo-400" />
              <h3 className="text-lg font-semibold text-indigo-900 dark:text-indigo-100">
                KI-Interpretation
              </h3>
            </div>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
              {interpretation}
            </p>
          </div>
        )}

        {/* Mood Tag */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <div className="flex items-center space-x-2 mb-4">
            <Tag className="h-5 w-5 text-purple-500" />
            <label className="text-lg font-semibold">Stimmung im Traum</label>
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Welche Stimmung hatte dein Traum?
          </p>
          <Controller
            name="mood_tag"
            control={control}
            render={({ field }) => (
              <div className="flex flex-wrap gap-2">
                {moodTags.map((tag) => (
                  <button
                    key={tag.value}
                    type="button"
                    onClick={() => field.onChange(field.value === tag.value ? '' : tag.value)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                      field.value === tag.value
                        ? tag.color + ' ring-2 ring-offset-2 ring-primary dark:ring-offset-gray-800'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                    }`}
                  >
                    {tag.label}
                  </button>
                ))}
              </div>
            )}
          />
        </div>

        {/* Lucid Dream Toggle */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow">
          <Controller
            name="lucid"
            control={control}
            render={({ field }) => (
              <label className="flex items-center justify-between cursor-pointer">
                <div className="flex items-center space-x-3">
                  <Eye className="h-5 w-5 text-indigo-500" />
                  <div>
                    <p className="text-lg font-semibold">Luzider Traum</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      War dies ein Klartraum? (Du warst dir bewusst, dass du träumst)
                    </p>
                  </div>
                </div>
                <div className="relative">
                  <input
                    type="checkbox"
                    {...field}
                    value={undefined}
                    checked={field.value}
                    className="sr-only"
                  />
                  <div
                    className={`block w-14 h-8 rounded-full transition-colors ${
                      field.value ? 'bg-primary' : 'bg-gray-300 dark:bg-gray-600'
                    }`}
                  >
                    <div
                      className={`absolute left-1 top-1 bg-white w-6 h-6 rounded-full transition-transform ${
                        field.value ? 'transform translate-x-6' : ''
                      }`}
                    />
                  </div>
                </div>
              </label>
            )}
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
            disabled={isLoading}
            className="flex-1 bg-primary hover:bg-primary/90 text-primary-foreground font-semibold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin -ml-1 mr-2 h-5 w-5" />
                Speichern...
              </>
            ) : (
              'Traum speichern'
            )}
          </button>
          <Link
            href="/dashboard/dreams"
            className="px-6 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg font-semibold hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-center"
          >
            Abbrechen
          </Link>
        </div>
      </form>
    </div>
  );
}
