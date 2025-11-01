// User Types
export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'patient' | 'therapist' | 'admin';
  is_verified: boolean;
  created_at: string;
  avatar_url?: string;
  timezone?: string;
  language?: string;
}

export interface UpdateProfileRequest {
  first_name?: string;
  last_name?: string;
  timezone?: string;
  language?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

export interface NotificationPreferences {
  email_notifications: boolean;
  push_notifications: boolean;
  therapy_reminders: boolean;
  mood_tracking_reminders: boolean;
  weekly_insights: boolean;
}

export interface PrivacySettings {
  profile_visibility: 'public' | 'private' | 'therapist_only';
  share_analytics: boolean;
  data_export_enabled: boolean;
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterPatientRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  date_of_birth?: string;
  emergency_contact?: string;
}

export interface RegisterTherapistRequest {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  license_number: string;
  specialization?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
  message: string;
}

// Mood Types
export interface MoodEntry {
  id: string;
  mood_score: number;
  energy_level: number;
  stress_level: number;
  sleep_hours: number;
  sleep_quality: number;
  activities: string[];
  notes?: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateMoodRequest {
  mood_score: number;
  energy_level: number;
  stress_level: number;
  sleep_hours: number;
  sleep_quality: number;
  activities: string[];
  notes?: string;
}

// Dream Types
export interface DreamEntry {
  id: string;
  title: string;
  content: string;
  mood_tag?: string;
  lucid: boolean;
  interpretation?: string;
  created_at: string;
  updated_at?: string;
}

export interface CreateDreamRequest {
  title: string;
  content: string;
  mood_tag?: string;
  lucid?: boolean;
}

export interface DreamInterpretationRequest {
  dream_text: string;
}

// Analytics Types
export interface MoodTrend {
  date: string;
  mood_score: number;
  energy_level: number;
  stress_level: number;
}

export interface OverviewStats {
  total_mood_entries: number;
  total_dream_entries: number;
  average_mood: number;
  average_energy: number;
  average_stress: number;
  average_sleep_hours: number;
}

export interface WellnessScore {
  score: number;
  trend: 'improving' | 'stable' | 'declining';
  factors: {
    mood: number;
    energy: number;
    sleep: number;
    stress: number;
  };
}

export interface MoodPatterns {
  bestDay: string;
  worstDay: string;
  bestTime: string;
  patterns: Array<{
    day: string;
    avgMood: number;
    count: number;
  }>;
}

export interface ActivityCorrelation {
  activity: string;
  impact: number;
  count: number;
}

export interface WeeklyInsight {
  weekStart: string;
  weekEnd: string;
  avgMood: number;
  totalEntries: number;
  insights: string[];
  recommendations: string[];
}

export interface MonthlyInsight {
  month: string;
  year: number;
  avgMood: number;
  totalEntries: number;
  insights: string[];
  recommendations: string[];
}

// AI Types
export interface AIMoodAnalysis {
  summary: string;
  insights: string[];
  recommendations: string[];
}

export interface AIChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
}

export interface AIChatSession {
  id: string;
  title: string;
  messages: AIChatMessage[];
  created_at: string;
  updated_at: string;
  last_message_preview?: string;
}

export interface AIChatRequest {
  message: string;
  context?: string;
  session_id?: string;
}

export interface AIChatResponse {
  response: string;
  timestamp: string;
  session_id?: string;
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ApiError {
  detail: string;
  status_code?: number;
}

// Admin Types
export interface AdminStats {
  totalUsers: number;
  activeTrainingJobs: number;
  totalModels: number;
  totalDatasets: number;
  systemHealth: string;
}

export interface AdminUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'patient' | 'therapist' | 'admin';
  is_verified: boolean;
  is_active: boolean;
  created_at: string;
}

export interface TrainingJob {
  id: string;
  model_type: string;
  status: string;
  progress: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  metrics?: {
    loss?: number;
    accuracy?: number;
    epoch?: number;
    total_epochs?: number;
  };
}

export interface AIModel {
  id: string;
  model_type: string;
  version: string;
  is_active: boolean;
  accuracy?: number;
  created_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  size: number;
  created_at: string;
}

// Therapy Types
export interface TherapyNote {
  id: string;
  title: string;
  content: string;
  technique?: string;
  session_date?: string;
  mood_before?: number;
  mood_after?: number;
  tags?: string[];
  is_private: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateTherapyNoteRequest {
  title: string;
  content: string;
  technique?: string;
  session_date?: string;
  mood_before?: number;
  mood_after?: number;
  tags?: string[];
  is_private?: boolean;
}

export interface TherapyTechnique {
  id: string;
  name: string;
  category: string;
  description: string;
}

export interface TherapySession {
  id: string;
  title: string;
  date: string;
  duration_minutes: number;
  notes?: string;
  goals?: string[];
  progress?: string;
  next_session?: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTherapySessionRequest {
  title: string;
  date: string;
  duration_minutes: number;
  notes?: string;
  goals?: string[];
  progress?: string;
  next_session?: string;
}
