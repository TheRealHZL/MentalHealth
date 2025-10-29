import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatDate(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleDateString('de-DE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  });
}

export function formatDateTime(date: string | Date): string {
  const d = typeof date === 'string' ? new Date(date) : date;
  return d.toLocaleString('de-DE', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

export function getMoodEmoji(score: number): string {
  if (score >= 9) return '😊';
  if (score >= 7) return '🙂';
  if (score >= 5) return '😐';
  if (score >= 3) return '😕';
  return '😢';
}

export function getMoodLabel(score: number): string {
  if (score >= 9) return 'Sehr gut';
  if (score >= 7) return 'Gut';
  if (score >= 5) return 'Neutral';
  if (score >= 3) return 'Nicht so gut';
  return 'Schlecht';
}

export function getEnergyLabel(level: number): string {
  if (level >= 8) return 'Sehr energiegeladen';
  if (level >= 6) return 'Energiegeladen';
  if (level >= 4) return 'Normal';
  if (level >= 2) return 'Müde';
  return 'Erschöpft';
}

export function getStressLabel(level: number): string {
  if (level >= 8) return 'Sehr gestresst';
  if (level >= 6) return 'Gestresst';
  if (level >= 4) return 'Moderat';
  if (level >= 2) return 'Leicht gestresst';
  return 'Entspannt';
}

export function getSleepQualityLabel(quality: number): string {
  if (quality >= 8) return 'Ausgezeichnet';
  if (quality >= 6) return 'Gut';
  if (quality >= 4) return 'Okay';
  if (quality >= 2) return 'Schlecht';
  return 'Sehr schlecht';
}
