/**
 * Key Management System
 *
 * Manages the lifecycle of encryption keys in the browser
 * - Master key derivation on login
 * - Secure key storage in memory
 * - Key rotation support
 * - Recovery key management
 *
 * SECURITY:
 * - Keys stored in memory only (never localStorage)
 * - Cleared on logout
 * - Session-based persistence
 */

import { createMasterKey, setupEncryption } from './encryption';
import { deriveMasterKey, generateSalt, exportKey, importKey } from './crypto-utils';
import type { EncryptionMetadata } from './encryption';

// ========================================
// Types
// ========================================

export interface KeyMetadata {
  salt: string;
  iterations: number;
  algorithm: string;
  version: number;
  hasRecoveryKey: boolean;
  createdAt: Date;
  lastRotation?: Date;
}

export interface StoredKeyInfo {
  masterKey: CryptoKey;
  metadata: KeyMetadata;
  derivedAt: Date;
}

export interface KeyDerivationProgress {
  status: 'idle' | 'deriving' | 'complete' | 'error';
  progress: number; // 0-100
  estimatedTimeMs?: number;
  error?: string;
}

// ========================================
// In-Memory Key Storage
// ========================================

class KeyStore {
  private masterKey: CryptoKey | null = null;
  private metadata: KeyMetadata | null = null;
  private derivedAt: Date | null = null;
  private recoveryKey: string | null = null;

  // Set master key
  setMasterKey(key: CryptoKey, metadata: KeyMetadata): void {
    this.masterKey = key;
    this.metadata = metadata;
    this.derivedAt = new Date();
  }

  // Get master key
  getMasterKey(): CryptoKey | null {
    return this.masterKey;
  }

  // Get metadata
  getMetadata(): KeyMetadata | null {
    return this.metadata;
  }

  // Check if key is available
  hasKey(): boolean {
    return this.masterKey !== null;
  }

  // Get key age in minutes
  getKeyAge(): number | null {
    if (!this.derivedAt) return null;
    const now = new Date();
    const ageMs = now.getTime() - this.derivedAt.getTime();
    return ageMs / (1000 * 60);
  }

  // Store recovery key (temporarily, for display to user)
  setRecoveryKey(key: string): void {
    this.recoveryKey = key;
  }

  // Get recovery key
  getRecoveryKey(): string | null {
    return this.recoveryKey;
  }

  // Clear recovery key after user has saved it
  clearRecoveryKey(): void {
    this.recoveryKey = null;
  }

  // Clear all keys (on logout)
  clear(): void {
    this.masterKey = null;
    this.metadata = null;
    this.derivedAt = null;
    this.recoveryKey = null;
  }

  // Export key to JWK (for session persistence)
  async exportToSession(): Promise<string | null> {
    if (!this.masterKey) return null;

    try {
      const jwk = await exportKey(this.masterKey);
      const sessionData = {
        jwk,
        metadata: this.metadata,
        derivedAt: this.derivedAt?.toISOString()
      };
      return JSON.stringify(sessionData);
    } catch (error) {
      console.error('Failed to export key to session:', error);
      return null;
    }
  }

  // Import key from JWK (session restore)
  async importFromSession(sessionData: string): Promise<boolean> {
    try {
      const data = JSON.parse(sessionData);
      const key = await importKey(data.jwk);

      this.masterKey = key;
      this.metadata = data.metadata;
      this.derivedAt = data.derivedAt ? new Date(data.derivedAt) : new Date();

      return true;
    } catch (error) {
      console.error('Failed to import key from session:', error);
      return false;
    }
  }
}

// Global key store instance
const keyStore = new KeyStore();

// ========================================
// Key Lifecycle Management
// ========================================

/**
 * Initialize encryption for new user (signup)
 *
 * @param password - User's password
 * @returns Setup metadata (to send to server)
 */
export async function initializeEncryption(
  password: string
): Promise<{ metadata: EncryptionMetadata; masterKey: CryptoKey }> {
  try {
    // Setup encryption (generates salt, derives key)
    const { metadata, masterKey } = await setupEncryption(password);

    // Store in memory
    keyStore.setMasterKey(masterKey, {
      salt: metadata.salt,
      iterations: metadata.iterations,
      algorithm: metadata.algorithm,
      version: metadata.version,
      hasRecoveryKey: false,
      createdAt: new Date()
    });

    return { metadata, masterKey };
  } catch (error) {
    console.error('Failed to initialize encryption:', error);
    throw new Error('Failed to initialize encryption');
  }
}

/**
 * Derive master key on login
 *
 * @param password - User's password
 * @param metadata - Encryption metadata from server
 * @param onProgress - Progress callback
 * @returns Master key
 */
export async function deriveKeyOnLogin(
  password: string,
  metadata: KeyMetadata,
  onProgress?: (progress: KeyDerivationProgress) => void
): Promise<CryptoKey> {
  try {
    // Notify start
    onProgress?.({
      status: 'deriving',
      progress: 0,
      estimatedTimeMs: (metadata.iterations / 600000) * 500 // Rough estimate
    });

    // Derive key (this takes time!)
    const masterKey = await createMasterKey(
      password,
      metadata.salt,
      metadata.iterations
    );

    // Store in memory
    keyStore.setMasterKey(masterKey, metadata);

    // Notify complete
    onProgress?.({
      status: 'complete',
      progress: 100
    });

    return masterKey;
  } catch (error) {
    console.error('Failed to derive key on login:', error);

    onProgress?.({
      status: 'error',
      progress: 0,
      error: 'Failed to derive encryption key'
    });

    throw new Error('Failed to derive encryption key');
  }
}

/**
 * Get current master key
 *
 * @returns Master key or null
 */
export function getMasterKey(): CryptoKey | null {
  return keyStore.getMasterKey();
}

/**
 * Check if master key is available
 *
 * @returns True if key exists in memory
 */
export function hasKey(): boolean {
  return keyStore.hasKey();
}

/**
 * Get key metadata
 *
 * @returns Key metadata or null
 */
export function getKeyMetadata(): KeyMetadata | null {
  return keyStore.getMetadata();
}

/**
 * Clear all keys (on logout)
 */
export function clearKeys(): void {
  keyStore.clear();
}

// ========================================
// Session Persistence
// ========================================

const SESSION_KEY = 'enc_session';

/**
 * Save key to sessionStorage (temporary)
 *
 * This allows keys to persist during page reloads
 * but clears when browser tab closes
 */
export async function saveToSession(): Promise<boolean> {
  try {
    const sessionData = await keyStore.exportToSession();
    if (!sessionData) return false;

    sessionStorage.setItem(SESSION_KEY, sessionData);
    return true;
  } catch (error) {
    console.error('Failed to save key to session:', error);
    return false;
  }
}

/**
 * Restore key from sessionStorage
 *
 * @returns True if successfully restored
 */
export async function restoreFromSession(): Promise<boolean> {
  try {
    const sessionData = sessionStorage.getItem(SESSION_KEY);
    if (!sessionData) return false;

    return await keyStore.importFromSession(sessionData);
  } catch (error) {
    console.error('Failed to restore key from session:', error);
    return false;
  }
}

/**
 * Clear session storage
 */
export function clearSession(): void {
  sessionStorage.removeItem(SESSION_KEY);
}

// ========================================
// Key Rotation
// ========================================

/**
 * Rotate encryption key (advanced feature)
 *
 * This generates a new salt and re-derives the key.
 * User must re-encrypt all data with the new key.
 *
 * @param password - User's current password
 * @returns New metadata
 */
export async function rotateKey(
  password: string
): Promise<EncryptionMetadata> {
  try {
    // Generate new salt
    const newSalt = generateSalt();

    // Derive new key
    const newKey = await createMasterKey(password, newSalt, 600000);

    // Update metadata
    const newMetadata: KeyMetadata = {
      salt: newSalt,
      iterations: 600000,
      algorithm: 'PBKDF2-SHA256',
      version: 1,
      hasRecoveryKey: false,
      createdAt: new Date(),
      lastRotation: new Date()
    };

    // Store new key
    keyStore.setMasterKey(newKey, newMetadata);

    return {
      salt: newSalt,
      iterations: 600000,
      algorithm: 'PBKDF2-SHA256',
      version: 1
    };
  } catch (error) {
    console.error('Key rotation failed:', error);
    throw new Error('Failed to rotate encryption key');
  }
}

// ========================================
// Recovery Key Management
// ========================================

/**
 * Generate recovery key for account recovery
 *
 * @returns Recovery key (user must save this!)
 */
export function generateRecoveryKey(): string {
  const recoveryKey = crypto.randomUUID() + crypto.randomUUID();
  keyStore.setRecoveryKey(recoveryKey);
  return recoveryKey;
}

/**
 * Get stored recovery key
 */
export function getRecoveryKey(): string | null {
  return keyStore.getRecoveryKey();
}

/**
 * Clear recovery key (after user confirms they've saved it)
 */
export function clearRecoveryKey(): void {
  keyStore.clearRecoveryKey();
}

// ========================================
// Validation & Utilities
// ========================================

/**
 * Validate that key is still valid
 *
 * Checks key age and performs test encryption
 */
export async function validateKey(): Promise<boolean> {
  try {
    const key = keyStore.getMasterKey();
    if (!key) return false;

    // Check key age (optional: implement timeout)
    const keyAge = keyStore.getKeyAge();
    if (keyAge && keyAge > 60) {
      // Key older than 60 minutes - might want to re-auth
      console.warn('Encryption key is old, consider re-authentication');
    }

    // Test encryption
    const testData = { test: 'validation' };
    const { encrypt } = await import('./encryption');
    await encrypt(testData, key);

    return true;
  } catch (error) {
    console.error('Key validation failed:', error);
    return false;
  }
}

/**
 * Get key status for UI
 */
export function getKeyStatus(): {
  available: boolean;
  ageMinutes: number | null;
  metadata: KeyMetadata | null;
} {
  return {
    available: keyStore.hasKey(),
    ageMinutes: keyStore.getKeyAge(),
    metadata: keyStore.getMetadata()
  };
}

// ========================================
// Export Everything
// ========================================

export const KeyManagement = {
  // Initialization
  initializeEncryption,
  deriveKeyOnLogin,

  // Access
  getMasterKey,
  hasKey,
  getKeyMetadata,
  clearKeys,

  // Session Persistence
  saveToSession,
  restoreFromSession,
  clearSession,

  // Key Rotation
  rotateKey,

  // Recovery
  generateRecoveryKey,
  getRecoveryKey,
  clearRecoveryKey,

  // Validation
  validateKey,
  getKeyStatus
};

export default KeyManagement;
