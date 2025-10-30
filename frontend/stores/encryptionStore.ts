/**
 * Encryption State Store (Zustand)
 *
 * Global state management for encryption status and operations
 * - Encryption availability
 * - Key derivation progress
 * - Encryption operations status
 * - Error handling
 */

import { create } from 'zustand';
import { devtools, persist } from 'zustand/middleware';
import KeyManagement from '../lib/keyManagement';
import type { KeyMetadata, KeyDerivationProgress } from '../lib/keyManagement';
import type { EncryptionMetadata } from '../lib/encryption';

// ========================================
// Types
// ========================================

export interface EncryptionState {
  // Key Status
  isEncryptionAvailable: boolean;
  keyMetadata: KeyMetadata | null;
  keyAge: number | null;

  // Key Derivation
  derivationProgress: KeyDerivationProgress;

  // Operations Status
  isEncrypting: boolean;
  isDecrypting: boolean;
  operationError: string | null;

  // Recovery
  recoveryKey: string | null;
  showRecoveryKey: boolean;

  // Actions
  initializeEncryption: (password: string) => Promise<EncryptionMetadata>;
  deriveKeyOnLogin: (password: string, metadata: KeyMetadata) => Promise<void>;
  restoreFromSession: () => Promise<boolean>;
  clearEncryption: () => void;

  // Recovery
  generateRecoveryKey: () => string;
  confirmRecoverySaved: () => void;

  // Status
  checkKeyStatus: () => void;
  setOperationStatus: (operation: 'encrypt' | 'decrypt', status: boolean) => void;
  setError: (error: string | null) => void;
}

// ========================================
// Store Definition
// ========================================

export const useEncryptionStore = create<EncryptionState>()(
  devtools(
    (set, get) => ({
      // Initial State
      isEncryptionAvailable: false,
      keyMetadata: null,
      keyAge: null,

      derivationProgress: {
        status: 'idle',
        progress: 0
      },

      isEncrypting: false,
      isDecrypting: false,
      operationError: null,

      recoveryKey: null,
      showRecoveryKey: false,

      // ========================================
      // Actions
      // ========================================

      /**
       * Initialize encryption for new user (signup)
       */
      initializeEncryption: async (password: string): Promise<EncryptionMetadata> => {
        try {
          set({ operationError: null });

          // Initialize encryption
          const { metadata, masterKey } = await KeyManagement.initializeEncryption(password);

          // Update state
          set({
            isEncryptionAvailable: true,
            keyMetadata: {
              salt: metadata.salt,
              iterations: metadata.iterations,
              algorithm: metadata.algorithm,
              version: metadata.version,
              hasRecoveryKey: false,
              createdAt: new Date()
            },
            keyAge: 0
          });

          // Save to session
          await KeyManagement.saveToSession();

          return metadata;
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to initialize encryption';
          set({
            operationError: errorMessage,
            isEncryptionAvailable: false
          });
          throw error;
        }
      },

      /**
       * Derive key on login
       */
      deriveKeyOnLogin: async (password: string, metadata: KeyMetadata): Promise<void> => {
        try {
          set({
            operationError: null,
            derivationProgress: {
              status: 'deriving',
              progress: 0,
              estimatedTimeMs: (metadata.iterations / 600000) * 500
            }
          });

          // Derive key with progress callback
          await KeyManagement.deriveKeyOnLogin(
            password,
            metadata,
            (progress) => {
              set({ derivationProgress: progress });
            }
          );

          // Update state
          set({
            isEncryptionAvailable: true,
            keyMetadata: metadata,
            keyAge: 0,
            derivationProgress: {
              status: 'complete',
              progress: 100
            }
          });

          // Save to session
          await KeyManagement.saveToSession();
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Failed to derive encryption key';
          set({
            operationError: errorMessage,
            isEncryptionAvailable: false,
            derivationProgress: {
              status: 'error',
              progress: 0,
              error: errorMessage
            }
          });
          throw error;
        }
      },

      /**
       * Restore key from session
       */
      restoreFromSession: async (): Promise<boolean> => {
        try {
          const restored = await KeyManagement.restoreFromSession();

          if (restored) {
            const status = KeyManagement.getKeyStatus();
            set({
              isEncryptionAvailable: status.available,
              keyMetadata: status.metadata,
              keyAge: status.ageMinutes
            });
          }

          return restored;
        } catch (error) {
          console.error('Failed to restore from session:', error);
          return false;
        }
      },

      /**
       * Clear encryption (logout)
       */
      clearEncryption: (): void => {
        KeyManagement.clearKeys();
        KeyManagement.clearSession();

        set({
          isEncryptionAvailable: false,
          keyMetadata: null,
          keyAge: null,
          derivationProgress: {
            status: 'idle',
            progress: 0
          },
          operationError: null,
          recoveryKey: null,
          showRecoveryKey: false
        });
      },

      /**
       * Generate recovery key
       */
      generateRecoveryKey: (): string => {
        const recoveryKey = KeyManagement.generateRecoveryKey();

        set({
          recoveryKey,
          showRecoveryKey: true
        });

        return recoveryKey;
      },

      /**
       * Confirm recovery key has been saved
       */
      confirmRecoverySaved: (): void => {
        KeyManagement.clearRecoveryKey();

        set({
          recoveryKey: null,
          showRecoveryKey: false,
          keyMetadata: get().keyMetadata ? {
            ...get().keyMetadata!,
            hasRecoveryKey: true
          } : null
        });
      },

      /**
       * Check and update key status
       */
      checkKeyStatus: (): void => {
        const status = KeyManagement.getKeyStatus();

        set({
          isEncryptionAvailable: status.available,
          keyMetadata: status.metadata,
          keyAge: status.ageMinutes
        });
      },

      /**
       * Set operation status (encrypt/decrypt in progress)
       */
      setOperationStatus: (operation: 'encrypt' | 'decrypt', status: boolean): void => {
        if (operation === 'encrypt') {
          set({ isEncrypting: status });
        } else {
          set({ isDecrypting: status });
        }
      },

      /**
       * Set error message
       */
      setError: (error: string | null): void => {
        set({ operationError: error });
      }
    }),
    {
      name: 'EncryptionStore',
      enabled: process.env.NODE_ENV === 'development'
    }
  )
);

// ========================================
// Selector Hooks (for better performance)
// ========================================

/**
 * Check if encryption is ready
 */
export const useEncryptionReady = () =>
  useEncryptionStore((state) => state.isEncryptionAvailable);

/**
 * Get key derivation progress
 */
export const useDerivationProgress = () =>
  useEncryptionStore((state) => state.derivationProgress);

/**
 * Get encryption error
 */
export const useEncryptionError = () =>
  useEncryptionStore((state) => state.operationError);

/**
 * Check if operations are in progress
 */
export const useOperationInProgress = () =>
  useEncryptionStore((state) => ({
    isEncrypting: state.isEncrypting,
    isDecrypting: state.isDecrypting,
    inProgress: state.isEncrypting || state.isDecrypting
  }));

/**
 * Get recovery key status
 */
export const useRecoveryKeyStatus = () =>
  useEncryptionStore((state) => ({
    recoveryKey: state.recoveryKey,
    showRecoveryKey: state.showRecoveryKey,
    hasRecoveryKey: state.keyMetadata?.hasRecoveryKey || false
  }));

/**
 * Get key metadata
 */
export const useKeyMetadata = () =>
  useEncryptionStore((state) => state.keyMetadata);

// ========================================
// Helper Functions
// ========================================

/**
 * Initialize encryption store on app start
 */
export async function initEncryptionStore(): Promise<void> {
  const store = useEncryptionStore.getState();

  // Try to restore from session
  await store.restoreFromSession();

  // Validate key if available
  if (store.isEncryptionAvailable) {
    const isValid = await KeyManagement.validateKey();
    if (!isValid) {
      store.clearEncryption();
    }
  }
}

/**
 * Periodic key status check (for UI updates)
 */
export function startKeyStatusMonitor(intervalMs: number = 60000): () => void {
  const store = useEncryptionStore.getState();

  const interval = setInterval(() => {
    store.checkKeyStatus();
  }, intervalMs);

  // Return cleanup function
  return () => clearInterval(interval);
}

export default useEncryptionStore;
