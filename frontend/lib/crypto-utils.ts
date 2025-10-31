/**
 * Cryptographic Utility Functions
 *
 * Low-level crypto operations using Web Crypto API
 * Used by the main encryption library
 */

// ========================================
// Constants
// ========================================

const PBKDF2_ITERATIONS = 600000; // OWASP recommended minimum
const SALT_LENGTH = 32; // 256 bits
const KEY_LENGTH = 256; // 256 bits for AES-256

// ========================================
// Key Derivation (PBKDF2)
// ========================================

/**
 * Derive AES-256 key from password using PBKDF2-SHA256
 *
 * @param password - User's password
 * @param salt - Base64-encoded salt
 * @param iterations - Number of PBKDF2 iterations (default 600000)
 * @returns CryptoKey for AES-GCM
 */
export async function deriveMasterKey(
  password: string,
  salt: string,
  iterations: number = PBKDF2_ITERATIONS
): Promise<CryptoKey> {
  try {
    // Convert password to key material
    const encoder = new TextEncoder();
    const passwordBuffer = encoder.encode(password);

    const importedKey = await crypto.subtle.importKey(
      'raw',
      passwordBuffer,
      { name: 'PBKDF2' },
      false,
      ['deriveBits', 'deriveKey']
    );

    // Convert salt from base64
    const saltBuffer = base64ToArrayBuffer(salt);

    // Derive AES-256 key using PBKDF2
    const derivedKey = await crypto.subtle.deriveKey(
      {
        name: 'PBKDF2',
        salt: saltBuffer,
        iterations: iterations,
        hash: 'SHA-256'
      },
      importedKey,
      {
        name: 'AES-GCM',
        length: KEY_LENGTH
      },
      true, // extractable
      ['encrypt', 'decrypt']
    );

    return derivedKey;
  } catch (error) {
    console.error('Key derivation failed:', error);
    throw new Error('Failed to derive master key from password');
  }
}

/**
 * Generate cryptographically secure random salt
 *
 * @returns Base64-encoded salt (32 bytes)
 */
export function generateSalt(): string {
  const saltArray = crypto.getRandomValues(new Uint8Array(SALT_LENGTH));
  return arrayBufferToBase64(saltArray.buffer);
}

/**
 * Generate random nonce for AES-GCM
 *
 * @returns Base64-encoded nonce (12 bytes)
 */
export function generateNonce(): string {
  const nonceArray = crypto.getRandomValues(new Uint8Array(12));
  return arrayBufferToBase64(nonceArray.buffer);
}

// ========================================
// Hashing Functions
// ========================================

/**
 * Hash data with SHA-256
 *
 * @param data - Data to hash (string or ArrayBuffer)
 * @returns Base64-encoded hash
 */
export async function sha256(data: string | ArrayBuffer): Promise<string> {
  if (typeof data === 'string') {
    const encoder = new TextEncoder();
    const dataBuffer = encoder.encode(data);
    const hashBuffer = await crypto.subtle.digest('SHA-256', dataBuffer);
    return arrayBufferToBase64(hashBuffer);
  } else {
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    return arrayBufferToBase64(hashBuffer);
  }
}

/**
 * Hash password for server authentication (NOT for encryption!)
 *
 * This is used for login/authentication, separate from encryption keys.
 * The server NEVER sees the encryption password directly.
 *
 * @param password - User's password
 * @param salt - Base64-encoded salt
 * @returns Base64-encoded hash
 */
export async function hashPasswordForAuth(
  password: string,
  salt: string
): Promise<string> {
  // Use PBKDF2 with different purpose
  const encoder = new TextEncoder();
  const passwordBuffer = encoder.encode(password);

  const importedKey = await crypto.subtle.importKey(
    'raw',
    passwordBuffer,
    { name: 'PBKDF2' },
    false,
    ['deriveBits']
  );

  const saltBuffer = base64ToArrayBuffer(salt);

  // Derive bits for authentication
  const derivedBits = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt: saltBuffer,
      iterations: 100000, // Fewer iterations for auth
      hash: 'SHA-256'
    },
    importedKey,
    256 // 256 bits
  );

  return arrayBufferToBase64(derivedBits);
}

// ========================================
// Password Strength Checking
// ========================================

export interface PasswordStrength {
  score: number; // 0-100
  feedback: string[];
  isStrong: boolean;
}

/**
 * Check password strength
 *
 * @param password - Password to check
 * @returns Strength assessment
 */
export function checkPasswordStrength(password: string): PasswordStrength {
  const feedback: string[] = [];
  let score = 0;

  // Length check
  if (password.length >= 12) {
    score += 25;
  } else {
    feedback.push('Password should be at least 12 characters');
  }

  if (password.length >= 16) {
    score += 15;
  }

  // Uppercase check
  if (/[A-Z]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include at least one uppercase letter');
  }

  // Lowercase check
  if (/[a-z]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include at least one lowercase letter');
  }

  // Number check
  if (/[0-9]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include at least one number');
  }

  // Special character check
  if (/[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]/.test(password)) {
    score += 15;
  } else {
    feedback.push('Include at least one special character');
  }

  // Common patterns check
  const commonPatterns = ['password', '123456', 'qwerty', 'letmein', 'admin'];
  const lowerPassword = password.toLowerCase();
  if (commonPatterns.some(pattern => lowerPassword.includes(pattern))) {
    score -= 30;
    feedback.push('Avoid common words and patterns');
  }

  // Repeated characters check
  if (/(.)\1{2,}/.test(password)) {
    score -= 10;
    feedback.push('Avoid repeating characters');
  }

  // Ensure score is in range
  score = Math.max(0, Math.min(100, score));

  return {
    score,
    feedback,
    isStrong: score >= 70
  };
}

// ========================================
// Random Generation
// ========================================

/**
 * Generate cryptographically secure random bytes
 *
 * @param length - Number of bytes
 * @returns Base64-encoded random bytes
 */
export function generateRandomBytes(length: number): string {
  const randomArray = crypto.getRandomValues(new Uint8Array(length));
  return arrayBufferToBase64(randomArray.buffer);
}

/**
 * Generate random UUID v4
 *
 * @returns UUID string
 */
export function generateUUID(): string {
  return crypto.randomUUID();
}

/**
 * Generate recovery key (256-bit random)
 *
 * @returns Base64-encoded recovery key
 */
export function generateRecoveryKey(): string {
  return generateRandomBytes(32); // 256 bits
}

// ========================================
// Encoding Utilities
// ========================================

/**
 * Convert ArrayBuffer to Base64
 */
export function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

/**
 * Convert Base64 to ArrayBuffer
 */
export function base64ToArrayBuffer(base64: string): ArrayBuffer {
  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return bytes.buffer;
}

/**
 * Convert string to ArrayBuffer
 */
export function stringToArrayBuffer(str: string): Uint8Array {
  const encoder = new TextEncoder();
  return encoder.encode(str);
}

/**
 * Convert ArrayBuffer to string
 */
export function arrayBufferToString(buffer: ArrayBuffer): string {
  const decoder = new TextDecoder();
  return decoder.decode(buffer);
}

// ========================================
// Timing-Safe Comparison
// ========================================

/**
 * Timing-safe string comparison
 *
 * Prevents timing attacks by comparing in constant time
 *
 * @param a - First string
 * @param b - Second string
 * @returns True if equal
 */
export function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) {
    return false;
  }

  let result = 0;
  for (let i = 0; i < a.length; i++) {
    result |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }

  return result === 0;
}

// ========================================
// Key Export/Import (for storage)
// ========================================

/**
 * Export CryptoKey to JSON Web Key format
 *
 * @param key - CryptoKey to export
 * @returns JWK object
 */
export async function exportKey(key: CryptoKey): Promise<JsonWebKey> {
  return await crypto.subtle.exportKey('jwk', key);
}

/**
 * Import CryptoKey from JSON Web Key format
 *
 * @param jwk - JWK object
 * @returns CryptoKey
 */
export async function importKey(jwk: JsonWebKey): Promise<CryptoKey> {
  return await crypto.subtle.importKey(
    'jwk',
    jwk,
    { name: 'AES-GCM', length: KEY_LENGTH },
    true,
    ['encrypt', 'decrypt']
  );
}

// ========================================
// Performance Utilities
// ========================================

/**
 * Measure PBKDF2 performance on current device
 *
 * This helps estimate key derivation time for UX
 *
 * @param iterations - Number of iterations to test
 * @returns Time in milliseconds
 */
export async function measurePBKDF2Performance(
  iterations: number = 10000
): Promise<number> {
  const start = performance.now();

  const password = 'test_password_for_benchmark';
  const salt = generateSalt();

  await deriveMasterKey(password, salt, iterations);

  const end = performance.now();
  return end - start;
}

/**
 * Estimate PBKDF2 time for given iterations
 *
 * @param iterations - Target iterations
 * @returns Estimated time in milliseconds
 */
export async function estimatePBKDF2Time(
  iterations: number = PBKDF2_ITERATIONS
): Promise<number> {
  // Benchmark with 10k iterations
  const time10k = await measurePBKDF2Performance(10000);

  // Linear extrapolation
  return (time10k / 10000) * iterations;
}

// ========================================
// Validation
// ========================================

/**
 * Validate base64 string
 */
export function isValidBase64(str: string): boolean {
  try {
    return btoa(atob(str)) === str;
  } catch {
    return false;
  }
}

/**
 * Validate salt format
 */
export function isValidSalt(salt: string): boolean {
  if (!isValidBase64(salt)) {
    return false;
  }

  const buffer = base64ToArrayBuffer(salt);
  return buffer.byteLength === SALT_LENGTH;
}

// ========================================
// Export Everything
// ========================================

export const CryptoUtils = {
  // Key Derivation
  deriveMasterKey,
  generateSalt,
  generateNonce,

  // Hashing
  sha256,
  hashPasswordForAuth,

  // Password Strength
  checkPasswordStrength,

  // Random Generation
  generateRandomBytes,
  generateUUID,
  generateRecoveryKey,

  // Encoding
  arrayBufferToBase64,
  base64ToArrayBuffer,
  stringToArrayBuffer,
  arrayBufferToString,

  // Security
  timingSafeEqual,

  // Key Management
  exportKey,
  importKey,

  // Performance
  measurePBKDF2Performance,
  estimatePBKDF2Time,

  // Validation
  isValidBase64,
  isValidSalt
};

export default CryptoUtils;
