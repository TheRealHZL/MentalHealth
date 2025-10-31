/**
 * Browser-Side Encryption Library (Web Crypto API)
 *
 * Zero-Knowledge End-to-End Encryption for MindBridge
 *
 * This library handles ALL encryption/decryption in the browser.
 * The server NEVER sees plaintext data!
 *
 * Algorithm: AES-256-GCM (Authenticated Encryption)
 * Key Derivation: PBKDF2-SHA256 (600,000 iterations)
 * Nonce: 96-bit random (crypto.getRandomValues)
 */

import { deriveMasterKey, generateSalt } from './crypto-utils';

// ========================================
// Types & Interfaces
// ========================================

export interface EncryptedPayload {
  ciphertext: string;  // Base64-encoded
  nonce: string;       // Base64-encoded (12 bytes)
  version: number;     // Encryption version
}

export interface EncryptionMetadata {
  salt: string;        // Base64-encoded
  iterations: number;
  algorithm: string;
  version: number;
}

export interface DecryptionResult {
  success: boolean;
  data?: any;
  error?: string;
}

// ========================================
// Constants
// ========================================

const ENCRYPTION_VERSION = 1;
const ALGORITHM = 'AES-GCM';
const KEY_LENGTH = 256;
const NONCE_LENGTH = 12; // 96 bits for GCM
const TAG_LENGTH = 128; // 128 bits for authentication tag

// ========================================
// Core Encryption Functions
// ========================================

/**
 * Encrypt data with AES-256-GCM
 *
 * @param data - Data to encrypt (will be JSON stringified)
 * @param masterKey - CryptoKey for AES-GCM
 * @returns Encrypted payload with ciphertext and nonce
 */
export async function encrypt(
  data: any,
  masterKey: CryptoKey
): Promise<EncryptedPayload> {
  try {
    // Convert data to JSON string
    const jsonString = JSON.stringify(data);

    // Convert to Uint8Array
    const encoder = new TextEncoder();
    const dataBytes = encoder.encode(jsonString);

    // Generate random nonce (96 bits for GCM)
    const nonce = crypto.getRandomValues(new Uint8Array(NONCE_LENGTH));

    // Encrypt with AES-GCM
    const ciphertextBuffer = await crypto.subtle.encrypt(
      {
        name: ALGORITHM,
        iv: nonce,
        tagLength: TAG_LENGTH
      },
      masterKey,
      dataBytes
    );

    // Convert to base64 for transport
    const ciphertext = arrayBufferToBase64(ciphertextBuffer);
    const nonceBase64 = arrayBufferToBase64(nonce);

    return {
      ciphertext,
      nonce: nonceBase64,
      version: ENCRYPTION_VERSION
    };
  } catch (error) {
    console.error('Encryption failed:', error);
    throw new Error('Failed to encrypt data');
  }
}

/**
 * Decrypt data with AES-256-GCM
 *
 * @param payload - Encrypted payload
 * @param masterKey - CryptoKey for AES-GCM
 * @returns Decrypted data
 */
export async function decrypt(
  payload: EncryptedPayload,
  masterKey: CryptoKey
): Promise<DecryptionResult> {
  try {
    // Validate payload
    if (!payload.ciphertext || !payload.nonce) {
      return {
        success: false,
        error: 'Invalid encrypted payload'
      };
    }

    // Check version
    if (payload.version !== ENCRYPTION_VERSION) {
      return {
        success: false,
        error: `Unsupported encryption version: ${payload.version}`
      };
    }

    // Convert from base64
    const ciphertext = base64ToArrayBuffer(payload.ciphertext);
    const nonce = base64ToArrayBuffer(payload.nonce);

    // Decrypt with AES-GCM
    const decryptedBuffer = await crypto.subtle.decrypt(
      {
        name: ALGORITHM,
        iv: nonce,
        tagLength: TAG_LENGTH
      },
      masterKey,
      ciphertext
    );

    // Convert back to string
    const decoder = new TextDecoder();
    const jsonString = decoder.decode(decryptedBuffer);

    // Parse JSON
    const data = JSON.parse(jsonString);

    return {
      success: true,
      data
    };
  } catch (error) {
    console.error('Decryption failed:', error);
    return {
      success: false,
      error: 'Failed to decrypt data. Wrong password or corrupted data.'
    };
  }
}

// ========================================
// Bulk Operations
// ========================================

/**
 * Encrypt multiple items (for batch operations)
 */
export async function encryptBatch(
  items: any[],
  masterKey: CryptoKey
): Promise<EncryptedPayload[]> {
  const results: EncryptedPayload[] = [];

  for (const item of items) {
    try {
      const encrypted = await encrypt(item, masterKey);
      results.push(encrypted);
    } catch (error) {
      console.error('Failed to encrypt item:', error);
      // Continue with other items
    }
  }

  return results;
}

/**
 * Decrypt multiple items (for batch operations)
 */
export async function decryptBatch(
  payloads: EncryptedPayload[],
  masterKey: CryptoKey
): Promise<any[]> {
  const results: any[] = [];

  for (const payload of payloads) {
    try {
      const result = await decrypt(payload, masterKey);
      if (result.success && result.data) {
        results.push(result.data);
      }
    } catch (error) {
      console.error('Failed to decrypt item:', error);
      // Continue with other items
    }
  }

  return results;
}

// ========================================
// Key Management
// ========================================

/**
 * Create encryption key from password
 *
 * @param password - User's password
 * @param salt - Salt for key derivation (base64)
 * @param iterations - PBKDF2 iterations (default 600000)
 * @returns CryptoKey for AES-GCM
 */
export async function createMasterKey(
  password: string,
  salt: string,
  iterations: number = 600000
): Promise<CryptoKey> {
  try {
    // Derive key using PBKDF2
    const derivedKey = await deriveMasterKey(password, salt, iterations);
    return derivedKey;
  } catch (error) {
    console.error('Master key creation failed:', error);
    throw new Error('Failed to create master key');
  }
}

/**
 * Setup encryption for new user
 *
 * @param password - User's password
 * @returns Encryption metadata (salt, iterations, etc.)
 */
export async function setupEncryption(
  password: string
): Promise<{ metadata: EncryptionMetadata; masterKey: CryptoKey }> {
  try {
    // Generate random salt
    const salt = generateSalt();

    // Create master key
    const masterKey = await createMasterKey(password, salt);

    // Return metadata
    const metadata: EncryptionMetadata = {
      salt,
      iterations: 600000,
      algorithm: 'PBKDF2-SHA256',
      version: ENCRYPTION_VERSION
    };

    return {
      metadata,
      masterKey
    };
  } catch (error) {
    console.error('Encryption setup failed:', error);
    throw new Error('Failed to setup encryption');
  }
}

// ========================================
// Utility Functions
// ========================================

/**
 * Convert ArrayBuffer or Uint8Array to Base64
 */
function arrayBufferToBase64(buffer: ArrayBuffer | Uint8Array): string {
  const bytes = buffer instanceof Uint8Array ? buffer : new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert Base64 to ArrayBuffer
 */
function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Estimate encryption time for user feedback
 */
export function estimateEncryptionTime(dataSize: number): number {
  // Rough estimate: ~1MB per 100ms on modern devices
  const sizeInMB = dataSize / (1024 * 1024);
  return Math.ceil(sizeInMB * 100);
}

/**
 * Validate encrypted payload structure
 */
export function validatePayload(payload: any): boolean {
  if (!payload || typeof payload !== 'object') {
    return false;
  }

  if (typeof payload.ciphertext !== 'string' || payload.ciphertext.length === 0) {
    return false;
  }

  if (typeof payload.nonce !== 'string' || payload.nonce.length === 0) {
    return false;
  }

  if (typeof payload.version !== 'number' || payload.version < 1) {
    return false;
  }

  return true;
}

/**
 * Generate fingerprint of encrypted data (for deduplication)
 */
export async function generateFingerprint(data: any): Promise<string> {
  const jsonString = JSON.stringify(data);
  const encoder = new TextEncoder();
  const dataBytes = encoder.encode(jsonString);

  const hashBuffer = await crypto.subtle.digest('SHA-256', dataBytes);
  return arrayBufferToBase64(hashBuffer);
}

// ========================================
// Export for convenience
// ========================================

export const EncryptionAPI = {
  encrypt,
  decrypt,
  encryptBatch,
  decryptBatch,
  createMasterKey,
  setupEncryption,
  validatePayload,
  generateFingerprint,
  estimateEncryptionTime
};

export default EncryptionAPI;
