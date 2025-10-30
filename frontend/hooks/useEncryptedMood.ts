/**
 * Encrypted Mood Entries Hook
 *
 * React hook for managing mood entries with automatic encryption
 * This demonstrates the pattern for integrating encryption into existing features
 *
 * Usage:
 * const { createMood, getMoods, isLoading, error } = useEncryptedMood();
 * await createMood({ mood_score: 7, notes: 'Feeling good!' });
 */

import { useState, useCallback } from 'react';
import { encryptedPost, encryptedGet, encryptedPut, encryptedDelete } from '@/lib/api-encrypted';
import { useEncryptionStore } from '@/stores/encryptionStore';
import type { MoodEntry, CreateMoodRequest, PaginatedResponse } from '@/types';

// ========================================
// Types
// ========================================

interface UseMoodResult {
  // Data
  moods: MoodEntry[];
  currentMood: MoodEntry | null;

  // State
  isLoading: boolean;
  isEncrypting: boolean;
  error: string | null;
  encryptionStatus: {
    isAvailable: boolean;
    isEnabled: boolean;
  };

  // Actions
  createMood: (data: CreateMoodRequest) => Promise<MoodEntry>;
  getMoods: (page?: number, size?: number) => Promise<PaginatedResponse<MoodEntry>>;
  getMoodById: (id: string) => Promise<MoodEntry>;
  updateMood: (id: string, data: Partial<CreateMoodRequest>) => Promise<MoodEntry>;
  deleteMood: (id: string) => Promise<void>;

  // Utility
  clearError: () => void;
}

// ========================================
// Hook Implementation
// ========================================

export function useEncryptedMood(): UseMoodResult {
  // State
  const [moods, setMoods] = useState<MoodEntry[]>([]);
  const [currentMood, setCurrentMood] = useState<MoodEntry | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Encryption state
  const isEncryptionAvailable = useEncryptionStore((state) => state.isEncryptionAvailable);
  const isEncrypting = useEncryptionStore((state) => state.isEncrypting);

  // ========================================
  // Actions
  // ========================================

  /**
   * Create mood entry (automatically encrypted)
   */
  const createMood = useCallback(async (data: CreateMoodRequest): Promise<MoodEntry> => {
    setIsLoading(true);
    setError(null);

    try {
      // Set encryption status
      useEncryptionStore.getState().setOperationStatus('encrypt', true);

      // Call encrypted API endpoint
      const moodEntry = await encryptedPost<MoodEntry>(
        '/mood/encrypted',
        data,
        {
          metadata: {
            created_at: new Date().toISOString(),
            source: 'web_app'
          }
        }
      );

      // Update local state
      setMoods((prev) => [moodEntry, ...prev]);
      setCurrentMood(moodEntry);

      return moodEntry;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create mood entry';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
      useEncryptionStore.getState().setOperationStatus('encrypt', false);
    }
  }, []);

  /**
   * Get mood entries (automatically decrypted)
   */
  const getMoods = useCallback(
    async (page: number = 1, size: number = 10): Promise<PaginatedResponse<MoodEntry>> => {
      setIsLoading(true);
      setError(null);

      try {
        // Set decryption status
        useEncryptionStore.getState().setOperationStatus('decrypt', true);

        // Call encrypted API endpoint
        const response = await encryptedGet<PaginatedResponse<MoodEntry>>(
          `/mood/encrypted?page=${page}&size=${size}`
        );

        // Update local state
        if (response.items) {
          setMoods(response.items);
        }

        return response;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to fetch mood entries';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
        useEncryptionStore.getState().setOperationStatus('decrypt', false);
      }
    },
    []
  );

  /**
   * Get single mood entry by ID (automatically decrypted)
   */
  const getMoodById = useCallback(async (id: string): Promise<MoodEntry> => {
    setIsLoading(true);
    setError(null);

    try {
      useEncryptionStore.getState().setOperationStatus('decrypt', true);

      const moodEntry = await encryptedGet<MoodEntry>(`/mood/encrypted/${id}`);

      setCurrentMood(moodEntry);
      return moodEntry;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch mood entry';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
      useEncryptionStore.getState().setOperationStatus('decrypt', false);
    }
  }, []);

  /**
   * Update mood entry (automatically encrypted)
   */
  const updateMood = useCallback(
    async (id: string, data: Partial<CreateMoodRequest>): Promise<MoodEntry> => {
      setIsLoading(true);
      setError(null);

      try {
        useEncryptionStore.getState().setOperationStatus('encrypt', true);

        const updatedMood = await encryptedPut<MoodEntry>(
          `/mood/encrypted/${id}`,
          data,
          {
            metadata: {
              updated_at: new Date().toISOString()
            }
          }
        );

        // Update local state
        setMoods((prev) =>
          prev.map((mood) => (mood.id === id ? updatedMood : mood))
        );
        setCurrentMood(updatedMood);

        return updatedMood;
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to update mood entry';
        setError(errorMessage);
        throw err;
      } finally {
        setIsLoading(false);
        useEncryptionStore.getState().setOperationStatus('encrypt', false);
      }
    },
    []
  );

  /**
   * Delete mood entry
   */
  const deleteMood = useCallback(async (id: string): Promise<void> => {
    setIsLoading(true);
    setError(null);

    try {
      await encryptedDelete(`/mood/encrypted/${id}`);

      // Update local state
      setMoods((prev) => prev.filter((mood) => mood.id !== id));
      if (currentMood?.id === id) {
        setCurrentMood(null);
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to delete mood entry';
      setError(errorMessage);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [currentMood]);

  /**
   * Clear error state
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // ========================================
  // Return Hook Interface
  // ========================================

  return {
    // Data
    moods,
    currentMood,

    // State
    isLoading,
    isEncrypting,
    error,
    encryptionStatus: {
      isAvailable: isEncryptionAvailable,
      isEnabled: isEncryptionAvailable
    },

    // Actions
    createMood,
    getMoods,
    getMoodById,
    updateMood,
    deleteMood,

    // Utility
    clearError
  };
}

// ========================================
// Additional Hooks for Other Features
// ========================================

/**
 * Similar pattern for Dreams
 */
export function useEncryptedDreams() {
  // Same pattern as useEncryptedMood, but for dreams
  // Implementation would be similar, just different endpoints
}

/**
 * Similar pattern for Therapy Notes
 */
export function useEncryptedTherapy() {
  // Same pattern for therapy session notes
}

/**
 * Similar pattern for AI Chat
 */
export function useEncryptedAIChat() {
  // Same pattern for AI chat messages
}

export default useEncryptedMood;
