# Zero-Knowledge Encryption Integration Guide

This guide explains how to use the Zero-Knowledge End-to-End Encryption system in MindBridge.

## Table of Contents

1. [Overview](#overview)
2. [Authentication Integration](#authentication-integration)
3. [API Integration](#api-integration)
4. [Form Integration](#form-integration)
5. [UI Components](#ui-components)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Overview

MindBridge uses **Zero-Knowledge End-to-End Encryption** to protect user data:

- All sensitive data is encrypted in the **browser** before being sent to the server
- The server **never sees plaintext data**
- Encryption keys are **derived from user's password** using PBKDF2-SHA256
- Keys are stored in **memory only** (never localStorage)
- **AES-256-GCM** for authenticated encryption

### Key Features

✅ Automatic encryption/decryption
✅ Backward compatible with legacy unencrypted data
✅ Session persistence (survives page reload)
✅ Recovery key system for account recovery
✅ Real-time progress tracking for key derivation
✅ Graceful error handling

---

## Authentication Integration

### Signup Flow

Use `encryptedRegisterPatient` or `encryptedRegisterTherapist` instead of regular registration:

```typescript
import { encryptedRegisterPatient } from '@/lib/auth-integration';
import { RecoveryKeyModal } from '@/components/RecoveryKeyModal';

// In your signup component
const handleSignup = async (formData) => {
  try {
    const response = await encryptedRegisterPatient({
      email: formData.email,
      password: formData.password,
      full_name: formData.fullName,
      // ... other fields
    });

    // Show recovery key modal
    if (response.needsRecoveryKey) {
      setShowRecoveryKeyModal(true);
    }

    // Continue with post-signup flow
    router.push('/dashboard');
  } catch (error) {
    console.error('Signup failed:', error);
  }
};
```

**What happens automatically:**
1. ✅ Generates random salt
2. ✅ Derives master key from password (600,000 PBKDF2 iterations)
3. ✅ Sends encryption metadata to server
4. ✅ Stores key in memory
5. ✅ Generates recovery key

### Login Flow

Use `encryptedLogin` instead of regular login:

```typescript
import { encryptedLogin } from '@/lib/auth-integration';
import { useEncryptionStore } from '@/stores/encryptionStore';

// In your login component
const handleLogin = async (credentials) => {
  try {
    const response = await encryptedLogin({
      email: credentials.email,
      password: credentials.password,
    });

    // Check encryption status
    if (response.encryptionInitialized) {
      console.log('✅ Encryption ready!');

      // Show recovery key prompt if user hasn't saved it
      if (response.needsRecoveryKey) {
        setShowRecoveryKeyPrompt(true);
      }
    } else {
      console.log('ℹ️ Legacy account without encryption');
    }

    router.push('/dashboard');
  } catch (error) {
    console.error('Login failed:', error);
  }
};
```

**What happens automatically:**
1. ✅ Authenticates with server
2. ✅ Fetches encryption metadata
3. ✅ Derives master key (with progress tracking!)
4. ✅ Stores key in memory
5. ✅ Validates key

### Logout Flow

Use `encryptedLogout` to clear encryption keys:

```typescript
import { encryptedLogout } from '@/lib/auth-integration';

const handleLogout = () => {
  encryptedLogout(); // Clears keys + logs out
};
```

### Session Restoration

Restore encryption session on app initialization:

```typescript
// In your root layout or _app.tsx
import { restoreEncryptionSession } from '@/lib/auth-integration';
import { useEffect } from 'react';

export default function RootLayout() {
  useEffect(() => {
    // Restore encryption session if available
    restoreEncryptionSession().then((restored) => {
      if (restored) {
        console.log('✅ Encryption session restored');
      }
    });
  }, []);

  return <>{children}</>;
}
```

---

## API Integration

### Using Encrypted API Wrapper

Replace direct API calls with encrypted versions:

#### Before (Unencrypted):
```typescript
import { apiClient } from '@/lib/api';

const mood = await apiClient.createMoodEntry(data);
```

#### After (Encrypted):
```typescript
import { encryptedPost } from '@/lib/api-encrypted';

const mood = await encryptedPost('/mood/encrypted', data);
```

### Available Functions

```typescript
import {
  encryptedPost,    // POST with encryption
  encryptedGet,     // GET with decryption
  encryptedPut,     // PUT with encryption
  encryptedDelete,  // DELETE
  encryptedGetBatch // Batch GET with decryption
} from '@/lib/api-encrypted';
```

### Example: Create Encrypted Mood Entry

```typescript
import { encryptedPost } from '@/lib/api-encrypted';
import type { MoodEntry, CreateMoodRequest } from '@/types';

const createMood = async (data: CreateMoodRequest): Promise<MoodEntry> => {
  try {
    const mood = await encryptedPost<MoodEntry>(
      '/mood/encrypted',  // Use encrypted endpoint
      data,
      {
        metadata: {
          created_at: new Date().toISOString(),
          source: 'web_app'
        }
      }
    );

    return mood;
  } catch (error) {
    console.error('Failed to create mood:', error);
    throw error;
  }
};
```

### Example: Get Encrypted Mood Entries

```typescript
import { encryptedGet } from '@/lib/api-encrypted';
import type { PaginatedResponse, MoodEntry } from '@/types';

const getMoods = async (): Promise<MoodEntry[]> => {
  try {
    const response = await encryptedGet<PaginatedResponse<MoodEntry>>(
      '/mood/encrypted?page=1&size=20'
    );

    return response.items;
  } catch (error) {
    console.error('Failed to fetch moods:', error);
    throw error;
  }
};
```

### Error Handling

```typescript
import { EncryptionError, ApiError, handleEncryptionError } from '@/lib/api-encrypted';

try {
  const mood = await encryptedPost('/mood/encrypted', data);
} catch (error) {
  if (error instanceof EncryptionError) {
    // Key not available or encryption failed
    alert('Please login again to continue.');
    router.push('/login');
  } else if (error instanceof ApiError) {
    // API request failed
    alert(`Error: ${error.message}`);
  } else {
    // Unknown error
    alert(handleEncryptionError(error));
  }
}
```

---

## Form Integration

### Using Encrypted Hooks

Use the `useEncryptedMood` hook (or create similar hooks for other features):

```typescript
import { useEncryptedMood } from '@/hooks/useEncryptedMood';

export function MoodForm() {
  const { createMood, isLoading, isEncrypting, error } = useEncryptedMood();

  const handleSubmit = async (formData) => {
    try {
      await createMood({
        mood_score: formData.moodScore,
        notes: formData.notes,
        activities: formData.activities,
      });

      alert('Mood entry saved (encrypted)!');
    } catch (error) {
      console.error('Failed to save mood:', error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Show encryption status */}
      {isEncrypting && <p>🔒 Encrypting...</p>}

      {/* Form fields */}
      <input type="number" name="moodScore" />
      <textarea name="notes" />

      <button disabled={isLoading}>
        {isLoading ? 'Saving...' : 'Save Mood'}
      </button>
    </form>
  );
}
```

### Creating Custom Encrypted Hooks

Follow this pattern for other features:

```typescript
import { encryptedPost, encryptedGet } from '@/lib/api-encrypted';
import { useEncryptionStore } from '@/stores/encryptionStore';
import { useState, useCallback } from 'react';

export function useEncryptedDreams() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createDream = useCallback(async (data) => {
    setIsLoading(true);
    setError(null);

    try {
      useEncryptionStore.getState().setOperationStatus('encrypt', true);

      const dream = await encryptedPost('/dreams/encrypted', data);

      return dream;
    } catch (err) {
      setError(err.message);
      throw err;
    } finally {
      setIsLoading(false);
      useEncryptionStore.getState().setOperationStatus('encrypt', false);
    }
  }, []);

  return { createDream, isLoading, error };
}
```

---

## UI Components

### Recovery Key Modal

Show after signup to prompt user to save recovery key:

```typescript
import { RecoveryKeyModal } from '@/components/RecoveryKeyModal';
import { useRecoveryKeyStatus } from '@/stores/encryptionStore';

export function SignupPage() {
  const { showRecoveryKey } = useRecoveryKeyStatus();

  return (
    <>
      {/* Signup form */}

      {/* Recovery key modal (shown automatically) */}
      {showRecoveryKey && (
        <RecoveryKeyModal
          onConfirm={() => {
            console.log('User saved recovery key');
            router.push('/dashboard');
          }}
          onCancel={() => {
            console.log('User skipped recovery key');
          }}
        />
      )}
    </>
  );
}
```

### Encryption Status Indicator

Show encryption status in your UI:

```typescript
import { useEncryptionReady, useEncryptionError } from '@/stores/encryptionStore';

export function EncryptionStatusBadge() {
  const isReady = useEncryptionReady();
  const error = useEncryptionError();

  if (error) {
    return <div className="text-red-600">🔓 Encryption Error</div>;
  }

  if (isReady) {
    return <div className="text-green-600">🔒 Encrypted</div>;
  }

  return <div className="text-gray-600">🔓 Not Encrypted</div>;
}
```

### Key Derivation Progress

Show progress during login (key derivation takes ~500ms):

```typescript
import { useDerivationProgress } from '@/stores/encryptionStore';

export function LoginForm() {
  const progress = useDerivationProgress();

  if (progress.status === 'deriving') {
    return (
      <div>
        <p>Deriving encryption key...</p>
        <progress value={progress.progress} max={100} />
        <p>{progress.estimatedTimeMs}ms estimated</p>
      </div>
    );
  }

  return <>{/* Login form */}</>;
}
```

---

## Testing

### Manual Testing Checklist

#### Signup Flow
- [ ] Create new account
- [ ] Verify recovery key modal appears
- [ ] Save recovery key
- [ ] Verify encryption metadata sent to server
- [ ] Check encryption status in UI

#### Login Flow
- [ ] Login with encrypted account
- [ ] Verify key derivation progress shown
- [ ] Verify encryption ready after login
- [ ] Check session persistence (reload page)

#### Data Operations
- [ ] Create encrypted mood entry
- [ ] View encrypted mood entries (decrypted automatically)
- [ ] Update encrypted mood entry
- [ ] Delete encrypted mood entry
- [ ] Verify encryption indicators in UI

#### Logout Flow
- [ ] Logout
- [ ] Verify keys cleared from memory
- [ ] Verify sessionStorage cleared
- [ ] Try to access encrypted data (should fail)

### Testing Encryption

```typescript
// Check if encryption is working
import KeyManagement from '@/lib/keyManagement';

// After login:
console.log('Key available:', KeyManagement.hasKey());
console.log('Key status:', KeyManagement.getKeyStatus());

// After logout:
console.log('Key cleared:', !KeyManagement.hasKey());
```

### Testing with DevTools

```typescript
// Open Redux DevTools (Zustand)
// Check EncryptionStore state:
{
  isEncryptionAvailable: true,
  keyMetadata: { salt: "...", iterations: 600000 },
  keyAge: 5, // minutes
  derivationProgress: { status: "complete", progress: 100 }
}
```

---

## Troubleshooting

### Common Issues

#### 1. "Encryption key not available"

**Cause:** User is not logged in or key was cleared.

**Solution:**
```typescript
import { restoreEncryptionSession } from '@/lib/auth-integration';

// Try to restore session
const restored = await restoreEncryptionSession();
if (!restored) {
  // Redirect to login
  router.push('/login');
}
```

#### 2. "Failed to decrypt data"

**Cause:** Wrong password, corrupted data, or key mismatch.

**Solution:**
- Verify user is using correct password
- Check that encryption metadata matches
- Validate key with `KeyManagement.validateKey()`

#### 3. Key derivation takes too long

**Cause:** 600,000 PBKDF2 iterations on slow device.

**Solution:**
- Show progress indicator during login
- Consider reducing iterations for testing (NOT for production)
- Use `estimatePBKDF2Time()` to show estimated time

#### 4. Session not persisting

**Cause:** SessionStorage cleared or disabled.

**Solution:**
```typescript
// Check sessionStorage availability
if (typeof window !== 'undefined' && window.sessionStorage) {
  console.log('SessionStorage available');
} else {
  console.warn('SessionStorage not available');
}
```

### Debugging

Enable detailed logging:

```typescript
// In crypto-utils.ts, encryption.ts, keyManagement.ts
// Uncomment console.log statements for debugging

// Check encryption store state
import { useEncryptionStore } from '@/stores/encryptionStore';

const state = useEncryptionStore.getState();
console.log('Encryption State:', {
  available: state.isEncryptionAvailable,
  keyAge: state.keyAge,
  progress: state.derivationProgress,
  error: state.operationError
});
```

---

## Best Practices

### ✅ DO:
- Use encrypted endpoints for all sensitive data
- Show encryption status to users
- Handle encryption errors gracefully
- Clear keys on logout
- Prompt users to save recovery keys
- Use progress indicators during key derivation

### ❌ DON'T:
- Store keys in localStorage (use memory only!)
- Skip error handling
- Ignore encryption errors
- Send plaintext sensitive data
- Hardcode encryption parameters
- Skip recovery key generation

---

## API Endpoints Reference

### Encrypted Endpoints

All encrypted endpoints follow the pattern: `/api/v1/{feature}/encrypted`

#### Mood Entries
- `POST /api/v1/mood/encrypted` - Create encrypted mood
- `GET /api/v1/mood/encrypted` - List encrypted moods
- `GET /api/v1/mood/encrypted/{id}` - Get single encrypted mood
- `PUT /api/v1/mood/encrypted/{id}` - Update encrypted mood
- `DELETE /api/v1/mood/encrypted/{id}` - Delete encrypted mood

#### Dream Entries
- `POST /api/v1/dreams/encrypted` - Create encrypted dream
- `GET /api/v1/dreams/encrypted` - List encrypted dreams
- `GET /api/v1/dreams/encrypted/{id}` - Get single encrypted dream
- `PUT /api/v1/dreams/encrypted/{id}` - Update encrypted dream
- `DELETE /api/v1/dreams/encrypted/{id}` - Delete encrypted dream

#### Therapy Notes
- `POST /api/v1/therapy/encrypted` - Create encrypted note
- `GET /api/v1/therapy/encrypted` - List encrypted notes
- `GET /api/v1/therapy/encrypted/{id}` - Get single encrypted note
- `PUT /api/v1/therapy/encrypted/{id}` - Update encrypted note
- `DELETE /api/v1/therapy/encrypted/{id}` - Delete encrypted note

#### AI Chat
- `POST /api/v1/ai/chat/encrypted` - Send encrypted chat message
- `GET /api/v1/ai/chat/encrypted/history` - Get encrypted chat history

#### Encryption Management
- `GET /api/v1/encryption/metadata` - Get user's encryption metadata
- `POST /api/v1/encryption/recovery-key` - Save encrypted recovery key
- `POST /api/v1/encryption/rotate-key` - Rotate encryption key (advanced)

---

## Summary

The Zero-Knowledge encryption system is designed to be:

1. **Transparent** - Works automatically once integrated
2. **Secure** - AES-256-GCM + PBKDF2-SHA256 (600K iterations)
3. **User-friendly** - Progress indicators, error messages
4. **Backward compatible** - Works with legacy unencrypted data
5. **Production-ready** - Comprehensive error handling

For questions or issues, refer to:
- `frontend/lib/encryption.ts` - Core encryption functions
- `frontend/lib/keyManagement.ts` - Key lifecycle management
- `frontend/stores/encryptionStore.ts` - Global state management
- `PHASE2_LOG.md` - Implementation log

**Happy encrypting! 🔒**
