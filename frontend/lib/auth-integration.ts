/**
 * Authentication Integration with Encryption
 *
 * Connects authentication flow with Zero-Knowledge encryption
 * - Initializes encryption on signup
 * - Derives keys on login
 * - Clears keys on logout
 * - Sends encryption metadata to server
 *
 * Usage:
 * import { encryptedLogin, encryptedRegister } from '@/lib/auth-integration';
 */

import { apiClient } from './api';
import KeyManagement from './keyManagement';
import { useEncryptionStore } from '@/stores/encryptionStore';
import type {
  LoginRequest,
  RegisterPatientRequest,
  RegisterTherapistRequest,
  AuthResponse
} from '@/types';
import type { EncryptionMetadata } from './encryption';

// ========================================
// Types
// ========================================

export interface EnhancedAuthResponse extends AuthResponse {
  encryptionInitialized: boolean;
  needsRecoveryKey: boolean;
}

export interface EncryptedRegisterRequest {
  userData: RegisterPatientRequest | RegisterTherapistRequest;
  encryptionMetadata: EncryptionMetadata;
}

// ========================================
// Enhanced Login with Key Derivation
// ========================================

/**
 * Login with automatic key derivation
 *
 * This function:
 * 1. Authenticates with server (gets token)
 * 2. Fetches encryption metadata from server
 * 3. Derives master key from password
 * 4. Stores key in memory
 *
 * @param credentials - Login credentials
 * @returns Authentication response
 */
export async function encryptedLogin(
  credentials: LoginRequest
): Promise<EnhancedAuthResponse> {
  try {
    // Step 1: Authenticate with server
    const authResponse = await apiClient.login(credentials);

    // Step 2: Try to get encryption metadata
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/encryption/metadata`,
        {
          headers: {
            'Authorization': `Bearer ${authResponse.access_token}`
          }
        }
      );

      if (response.ok) {
        const metadata = await response.json();

        // Step 3: Derive key from password
        const encryptionStore = useEncryptionStore.getState();
        await encryptionStore.deriveKeyOnLogin(credentials.password, {
          salt: metadata.salt,
          iterations: metadata.iterations,
          algorithm: metadata.algorithm,
          version: metadata.version,
          hasRecoveryKey: metadata.has_recovery_key || false,
          createdAt: new Date(metadata.created_at)
        });

        return {
          ...authResponse,
          encryptionInitialized: true,
          needsRecoveryKey: !metadata.has_recovery_key
        };
      }
    } catch (error) {
      console.warn('No encryption metadata found, continuing without encryption:', error);
    }

    // No encryption metadata - legacy account
    return {
      ...authResponse,
      encryptionInitialized: false,
      needsRecoveryKey: false
    };
  } catch (error) {
    console.error('Login failed:', error);
    throw error;
  }
}

// ========================================
// Enhanced Registration with Encryption Setup
// ========================================

/**
 * Register patient with encryption initialization
 *
 * This function:
 * 1. Generates salt and derives master key
 * 2. Sends user data + encryption metadata to server
 * 3. Stores key in memory
 * 4. Generates recovery key
 *
 * @param userData - Registration data
 * @returns Authentication response
 */
export async function encryptedRegisterPatient(
  userData: RegisterPatientRequest
): Promise<EnhancedAuthResponse> {
  try {
    // Step 1: Initialize encryption
    const encryptionStore = useEncryptionStore.getState();
    const metadata = await encryptionStore.initializeEncryption(userData.password);

    // Step 2: Register with server (send encryption metadata)
    const registrationData = {
      ...userData,
      encryption_salt: metadata.salt,
      encryption_iterations: metadata.iterations,
      encryption_algorithm: metadata.algorithm,
      encryption_version: metadata.version
    };

    const authResponse = await apiClient.registerPatient(registrationData as any);

    // Step 3: Generate recovery key
    const recoveryKey = encryptionStore.generateRecoveryKey();

    return {
      ...authResponse,
      encryptionInitialized: true,
      needsRecoveryKey: true // User must save recovery key
    };
  } catch (error) {
    console.error('Registration failed:', error);

    // Clean up encryption if registration fails
    const encryptionStore = useEncryptionStore.getState();
    encryptionStore.clearEncryption();

    throw error;
  }
}

/**
 * Register therapist with encryption initialization
 *
 * @param userData - Registration data
 * @returns Authentication response
 */
export async function encryptedRegisterTherapist(
  userData: RegisterTherapistRequest
): Promise<EnhancedAuthResponse> {
  try {
    // Step 1: Initialize encryption
    const encryptionStore = useEncryptionStore.getState();
    const metadata = await encryptionStore.initializeEncryption(userData.password);

    // Step 2: Register with server (send encryption metadata)
    const registrationData = {
      ...userData,
      encryption_salt: metadata.salt,
      encryption_iterations: metadata.iterations,
      encryption_algorithm: metadata.algorithm,
      encryption_version: metadata.version
    };

    const authResponse = await apiClient.registerTherapist(registrationData as any);

    // Step 3: Generate recovery key
    const recoveryKey = encryptionStore.generateRecoveryKey();

    return {
      ...authResponse,
      encryptionInitialized: true,
      needsRecoveryKey: true // User must save recovery key
    };
  } catch (error) {
    console.error('Registration failed:', error);

    // Clean up encryption if registration fails
    const encryptionStore = useEncryptionStore.getState();
    encryptionStore.clearEncryption();

    throw error;
  }
}

// ========================================
// Enhanced Logout with Key Clearing
// ========================================

/**
 * Logout with automatic key clearing
 *
 * This function:
 * 1. Clears encryption keys from memory
 * 2. Clears session storage
 * 3. Logs out from server
 *
 * @returns void
 */
export function encryptedLogout(): void {
  try {
    // Step 1: Clear encryption keys
    const encryptionStore = useEncryptionStore.getState();
    encryptionStore.clearEncryption();

    // Step 2: Logout from API
    apiClient.logout();
  } catch (error) {
    console.error('Logout failed:', error);

    // Force clear even if error occurs
    KeyManagement.clearKeys();
    KeyManagement.clearSession();
  }
}

// ========================================
// Recovery Key Management
// ========================================

/**
 * Save recovery key to server (encrypted with user's key)
 *
 * @param recoveryKey - Recovery key to save
 * @returns Success status
 */
export async function saveRecoveryKey(recoveryKey: string): Promise<boolean> {
  try {
    const masterKey = KeyManagement.getMasterKey();
    if (!masterKey) {
      throw new Error('Encryption key not available');
    }

    // Encrypt recovery key with master key
    const { encrypt } = await import('./encryption');
    const encryptedRecoveryKey = await encrypt({ recoveryKey }, masterKey);

    // Send to server
    const token = localStorage.getItem('token');
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/encryption/recovery-key`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          encryptedData: encryptedRecoveryKey
        })
      }
    );

    if (!response.ok) {
      throw new Error('Failed to save recovery key');
    }

    // Mark as saved in store
    const encryptionStore = useEncryptionStore.getState();
    encryptionStore.confirmRecoverySaved();

    return true;
  } catch (error) {
    console.error('Failed to save recovery key:', error);
    return false;
  }
}

/**
 * Confirm recovery key has been saved by user
 *
 * @returns void
 */
export function confirmRecoveryKeySaved(): void {
  const encryptionStore = useEncryptionStore.getState();
  encryptionStore.confirmRecoverySaved();
}

// ========================================
// Session Restoration
// ========================================

/**
 * Restore encryption session on app start
 *
 * This should be called when the app initializes
 * to restore encryption keys from session storage
 *
 * @returns Success status
 */
export async function restoreEncryptionSession(): Promise<boolean> {
  try {
    const encryptionStore = useEncryptionStore.getState();
    const restored = await encryptionStore.restoreFromSession();

    if (restored) {
      // Validate the restored key
      const isValid = await KeyManagement.validateKey();
      if (!isValid) {
        console.warn('Restored key is invalid, clearing encryption');
        encryptionStore.clearEncryption();
        return false;
      }
    }

    return restored;
  } catch (error) {
    console.error('Failed to restore encryption session:', error);
    return false;
  }
}

// ========================================
// Utility Functions
// ========================================

/**
 * Check if user has encryption enabled
 *
 * @returns True if encryption is available
 */
export function hasEncryption(): boolean {
  const encryptionStore = useEncryptionStore.getState();
  return encryptionStore.isEncryptionAvailable;
}

/**
 * Get encryption status for UI
 *
 * @returns Encryption status
 */
export function getEncryptionInfo(): {
  isAvailable: boolean;
  keyAge: number | null;
  needsRecoveryKey: boolean;
  needsReauth: boolean;
} {
  const encryptionStore = useEncryptionStore.getState();
  const keyAge = encryptionStore.keyAge;

  return {
    isAvailable: encryptionStore.isEncryptionAvailable,
    keyAge,
    needsRecoveryKey: !encryptionStore.keyMetadata?.hasRecoveryKey,
    needsReauth: keyAge ? keyAge > 60 : false
  };
}

/**
 * Request user to re-authenticate for security
 *
 * @returns void
 */
export function requestReauth(): void {
  if (typeof window !== 'undefined') {
    // Clear encryption but keep auth token
    const encryptionStore = useEncryptionStore.getState();
    encryptionStore.clearEncryption();

    // Redirect to re-auth page (or show modal)
    window.location.href = '/reauth';
  }
}

// ========================================
// Export Everything
// ========================================

export const EncryptedAuth = {
  login: encryptedLogin,
  registerPatient: encryptedRegisterPatient,
  registerTherapist: encryptedRegisterTherapist,
  logout: encryptedLogout,
  saveRecoveryKey,
  confirmRecoveryKeySaved,
  restoreSession: restoreEncryptionSession,
  hasEncryption,
  getInfo: getEncryptionInfo,
  requestReauth
};

export default EncryptedAuth;
