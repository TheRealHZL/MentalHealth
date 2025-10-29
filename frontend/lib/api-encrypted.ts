/**
 * Encrypted API Wrapper
 *
 * Wraps API calls with automatic encryption/decryption
 * - Encrypts data before sending to server
 * - Decrypts data received from server
 * - Handles both encrypted and legacy unencrypted data
 * - Graceful error handling
 *
 * Usage:
 * import { encryptedPost, encryptedGet } from '@/lib/api-encrypted';
 * const mood = await encryptedPost('/api/mood-entries', moodData);
 */

import { encrypt, decrypt, type EncryptedPayload } from './encryption';
import KeyManagement from './keyManagement';

// ========================================
// Types
// ========================================

export interface EncryptedRequest {
  encryptedData: EncryptedPayload;
  metadata?: Record<string, any>; // Non-sensitive metadata (e.g., timestamps)
}

export interface EncryptedResponse<T = any> {
  success: boolean;
  data?: T;
  encryptedData?: EncryptedPayload;
  error?: string;
  isEncrypted: boolean;
}

export interface ApiOptions extends RequestInit {
  skipEncryption?: boolean; // For public endpoints
  metadata?: Record<string, any>; // Non-sensitive metadata
}

// ========================================
// Error Handling
// ========================================

export class EncryptionError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'EncryptionError';
  }
}

export class ApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public response?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// ========================================
// Core API Functions
// ========================================

/**
 * POST with automatic encryption
 *
 * @param url - API endpoint
 * @param data - Data to encrypt and send
 * @param options - Fetch options
 * @returns Decrypted response data
 */
export async function encryptedPost<T = any>(
  url: string,
  data: any,
  options?: ApiOptions
): Promise<T> {
  try {
    // Get master key
    const masterKey = KeyManagement.getMasterKey();
    if (!masterKey && !options?.skipEncryption) {
      throw new EncryptionError('Encryption key not available. Please login again.');
    }

    let body: any;

    // Encrypt data if key is available
    if (masterKey && !options?.skipEncryption) {
      const encryptedPayload = await encrypt(data, masterKey);

      body = JSON.stringify({
        encryptedData: encryptedPayload,
        metadata: options?.metadata || {}
      } as EncryptedRequest);
    } else {
      // Fallback to unencrypted (for backward compatibility)
      body = JSON.stringify(data);
    }

    // Make request
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      },
      body,
      ...options
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `API request failed: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    const responseData: EncryptedResponse<T> = await response.json();

    // Decrypt if response is encrypted
    if (responseData.isEncrypted && responseData.encryptedData && masterKey) {
      const decryptResult = await decrypt(responseData.encryptedData, masterKey);

      if (!decryptResult.success) {
        throw new EncryptionError(decryptResult.error || 'Failed to decrypt response');
      }

      return decryptResult.data as T;
    }

    // Return unencrypted data (legacy support)
    return responseData.data as T;
  } catch (error) {
    if (error instanceof EncryptionError || error instanceof ApiError) {
      throw error;
    }

    console.error('Encrypted POST failed:', error);
    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown error occurred'
    );
  }
}

/**
 * GET with automatic decryption
 *
 * @param url - API endpoint
 * @param options - Fetch options
 * @returns Decrypted response data
 */
export async function encryptedGet<T = any>(
  url: string,
  options?: ApiOptions
): Promise<T> {
  try {
    // Get master key
    const masterKey = KeyManagement.getMasterKey();
    if (!masterKey && !options?.skipEncryption) {
      throw new EncryptionError('Encryption key not available. Please login again.');
    }

    // Make request
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      },
      ...options
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `API request failed: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    const responseData: EncryptedResponse<T> = await response.json();

    // Decrypt if response is encrypted
    if (responseData.isEncrypted && responseData.encryptedData && masterKey) {
      const decryptResult = await decrypt(responseData.encryptedData, masterKey);

      if (!decryptResult.success) {
        throw new EncryptionError(decryptResult.error || 'Failed to decrypt response');
      }

      return decryptResult.data as T;
    }

    // Return unencrypted data (legacy support)
    return responseData.data as T;
  } catch (error) {
    if (error instanceof EncryptionError || error instanceof ApiError) {
      throw error;
    }

    console.error('Encrypted GET failed:', error);
    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown error occurred'
    );
  }
}

/**
 * PUT with automatic encryption
 */
export async function encryptedPut<T = any>(
  url: string,
  data: any,
  options?: ApiOptions
): Promise<T> {
  try {
    const masterKey = KeyManagement.getMasterKey();
    if (!masterKey && !options?.skipEncryption) {
      throw new EncryptionError('Encryption key not available. Please login again.');
    }

    let body: any;

    if (masterKey && !options?.skipEncryption) {
      const encryptedPayload = await encrypt(data, masterKey);
      body = JSON.stringify({
        encryptedData: encryptedPayload,
        metadata: options?.metadata || {}
      } as EncryptedRequest);
    } else {
      body = JSON.stringify(data);
    }

    const response = await fetch(url, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      },
      body,
      ...options
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `API request failed: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    const responseData: EncryptedResponse<T> = await response.json();

    if (responseData.isEncrypted && responseData.encryptedData && masterKey) {
      const decryptResult = await decrypt(responseData.encryptedData, masterKey);
      if (!decryptResult.success) {
        throw new EncryptionError(decryptResult.error || 'Failed to decrypt response');
      }
      return decryptResult.data as T;
    }

    return responseData.data as T;
  } catch (error) {
    if (error instanceof EncryptionError || error instanceof ApiError) {
      throw error;
    }
    console.error('Encrypted PUT failed:', error);
    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown error occurred'
    );
  }
}

/**
 * DELETE with optional encryption
 */
export async function encryptedDelete<T = any>(
  url: string,
  options?: ApiOptions
): Promise<T> {
  try {
    const response = await fetch(url, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      },
      ...options
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `API request failed: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    const responseData: EncryptedResponse<T> = await response.json();
    return responseData.data as T;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    console.error('Encrypted DELETE failed:', error);
    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown error occurred'
    );
  }
}

// ========================================
// Batch Operations
// ========================================

/**
 * Batch GET with decryption
 *
 * @param url - API endpoint for batch data
 * @param options - Fetch options
 * @returns Array of decrypted items
 */
export async function encryptedGetBatch<T = any>(
  url: string,
  options?: ApiOptions
): Promise<T[]> {
  try {
    const masterKey = KeyManagement.getMasterKey();
    if (!masterKey && !options?.skipEncryption) {
      throw new EncryptionError('Encryption key not available. Please login again.');
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {})
      },
      ...options
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `API request failed: ${response.statusText}`,
        response.status,
        errorData
      );
    }

    const responseData = await response.json();

    // Handle array of encrypted items
    if (Array.isArray(responseData)) {
      const decryptedItems: T[] = [];

      for (const item of responseData) {
        if (item.isEncrypted && item.encryptedData && masterKey) {
          const decryptResult = await decrypt(item.encryptedData, masterKey);
          if (decryptResult.success && decryptResult.data) {
            decryptedItems.push(decryptResult.data as T);
          }
        } else if (item.data) {
          // Legacy unencrypted data
          decryptedItems.push(item.data as T);
        }
      }

      return decryptedItems;
    }

    return [];
  } catch (error) {
    if (error instanceof EncryptionError || error instanceof ApiError) {
      throw error;
    }
    console.error('Encrypted batch GET failed:', error);
    throw new ApiError(
      error instanceof Error ? error.message : 'Unknown error occurred'
    );
  }
}

// ========================================
// Utility Functions
// ========================================

/**
 * Check if encryption is available
 */
export function isEncryptionAvailable(): boolean {
  return KeyManagement.hasKey();
}

/**
 * Get encryption status for UI
 */
export function getEncryptionStatus(): {
  available: boolean;
  keyAge: number | null;
  needsReauth: boolean;
} {
  const status = KeyManagement.getKeyStatus();
  return {
    available: status.available,
    keyAge: status.ageMinutes,
    needsReauth: status.ageMinutes ? status.ageMinutes > 60 : false
  };
}

/**
 * Handle encryption errors with user-friendly messages
 */
export function handleEncryptionError(error: unknown): string {
  if (error instanceof EncryptionError) {
    return error.message;
  }

  if (error instanceof ApiError) {
    if (error.statusCode === 401) {
      return 'Please login again to continue.';
    }
    if (error.statusCode === 403) {
      return 'You do not have permission to perform this action.';
    }
    return error.message;
  }

  return 'An unexpected error occurred. Please try again.';
}

// ========================================
// Export Everything
// ========================================

export const EncryptedAPI = {
  post: encryptedPost,
  get: encryptedGet,
  put: encryptedPut,
  delete: encryptedDelete,
  getBatch: encryptedGetBatch,
  isAvailable: isEncryptionAvailable,
  getStatus: getEncryptionStatus,
  handleError: handleEncryptionError
};

export default EncryptedAPI;
