/**
 * Recovery Key Modal Component
 *
 * Displays the recovery key to the user after signup/registration
 * Forces user to save/copy the key before continuing
 *
 * CRITICAL: Users MUST save this key - without it, encrypted data is unrecoverable!
 */

'use client';

import { useState } from 'react';
import { useRecoveryKeyStatus } from '@/stores/encryptionStore';
import { confirmRecoveryKeySaved } from '@/lib/auth-integration';

// ========================================
// Types
// ========================================

interface RecoveryKeyModalProps {
  onConfirm?: () => void;
  onCancel?: () => void;
}

// ========================================
// Component
// ========================================

export function RecoveryKeyModal({ onConfirm, onCancel }: RecoveryKeyModalProps) {
  const { recoveryKey, showRecoveryKey } = useRecoveryKeyStatus();
  const [copied, setCopied] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [saved, setSaved] = useState(false);

  // Don't show modal if no recovery key
  if (!showRecoveryKey || !recoveryKey) {
    return null;
  }

  // ========================================
  // Handlers
  // ========================================

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(recoveryKey);
      setCopied(true);

      // Reset copied state after 3 seconds
      setTimeout(() => setCopied(false), 3000);
    } catch (error) {
      console.error('Failed to copy recovery key:', error);
      alert('Failed to copy to clipboard. Please copy manually.');
    }
  };

  const handleDownload = () => {
    const blob = new Blob([
      `MindBridge Recovery Key\n`,
      `======================\n\n`,
      `Recovery Key: ${recoveryKey}\n\n`,
      `IMPORTANT:\n`,
      `- Keep this key in a safe place\n`,
      `- You need this key to recover your account if you forget your password\n`,
      `- Without this key, your encrypted data cannot be recovered\n`,
      `- Do not share this key with anyone\n\n`,
      `Generated: ${new Date().toISOString()}\n`
    ], { type: 'text/plain' });

    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mindbridge-recovery-key-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);

    setSaved(true);
  };

  const handleConfirm = () => {
    if (!confirmed) {
      alert('Please confirm that you have saved your recovery key.');
      return;
    }

    // Mark recovery key as saved
    confirmRecoveryKeySaved();

    // Call parent callback
    onConfirm?.();
  };

  const handleCancel = () => {
    if (!confirmed) {
      const shouldCancel = window.confirm(
        'Are you sure? Without saving your recovery key, you will not be able to recover your account if you forget your password.'
      );
      if (!shouldCancel) return;
    }

    onCancel?.();
  };

  // ========================================
  // Render
  // ========================================

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-yellow-100 rounded-full flex items-center justify-center">
            <svg
              className="w-6 h-6 text-yellow-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Save Your Recovery Key</h2>
            <p className="text-sm text-gray-600">This is the only time you'll see this key</p>
          </div>
        </div>

        {/* Warning */}
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg
                className="h-5 w-5 text-yellow-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">Critical: Save This Key</h3>
              <div className="mt-2 text-sm text-yellow-700">
                <ul className="list-disc pl-5 space-y-1">
                  <li>You need this key to recover your account if you forget your password</li>
                  <li>Without this key, your encrypted data cannot be recovered</li>
                  <li>We cannot help you recover this key - keep it safe!</li>
                </ul>
              </div>
            </div>
          </div>
        </div>

        {/* Recovery Key Display */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Recovery Key
          </label>
          <div className="relative">
            <input
              type="text"
              readOnly
              value={recoveryKey}
              className="w-full px-4 py-3 font-mono text-sm bg-gray-50 border border-gray-300 rounded-lg focus:outline-none"
            />
            <button
              onClick={handleCopy}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 px-3 py-1 text-sm font-medium text-blue-600 hover:text-blue-700 focus:outline-none"
            >
              {copied ? '✓ Copied!' : 'Copy'}
            </button>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-6">
          <button
            onClick={handleDownload}
            className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors"
          >
            {saved ? '✓ Downloaded' : 'Download as File'}
          </button>
          <button
            onClick={handleCopy}
            className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          >
            {copied ? '✓ Copied to Clipboard' : 'Copy to Clipboard'}
          </button>
        </div>

        {/* Confirmation Checkbox */}
        <div className="mb-6">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="mt-1 w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="text-sm text-gray-700">
              I have saved my recovery key in a safe place. I understand that without this key,
              I will not be able to recover my encrypted data if I forget my password.
            </span>
          </label>
        </div>

        {/* Footer Buttons */}
        <div className="flex gap-3">
          <button
            onClick={handleCancel}
            className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors"
          >
            I'll Save It Later
          </button>
          <button
            onClick={handleConfirm}
            disabled={!confirmed}
            className={`flex-1 px-4 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors ${
              confirmed
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            I've Saved My Key, Continue
          </button>
        </div>

        {/* Security Info */}
        <div className="mt-6 pt-6 border-t border-gray-200">
          <h4 className="text-sm font-medium text-gray-900 mb-2">Why do I need this?</h4>
          <p className="text-sm text-gray-600">
            MindBridge uses Zero-Knowledge encryption to protect your privacy. Your data is
            encrypted in your browser before it's sent to our servers. This means we never see
            your sensitive information, but it also means we can't recover your data if you
            lose access to your account. Your recovery key is the only way to restore your
            encrypted data.
          </p>
        </div>
      </div>
    </div>
  );
}

// ========================================
// Compact Version for Settings
// ========================================

export function RecoveryKeyDisplay({ recoveryKey }: { recoveryKey: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(recoveryKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 3000);
    } catch (error) {
      console.error('Failed to copy:', error);
    }
  };

  return (
    <div className="bg-gray-50 p-4 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-gray-700">Recovery Key</span>
        <button
          onClick={handleCopy}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          {copied ? '✓ Copied' : 'Copy'}
        </button>
      </div>
      <code className="block text-xs font-mono text-gray-600 break-all">
        {recoveryKey}
      </code>
    </div>
  );
}

export default RecoveryKeyModal;
