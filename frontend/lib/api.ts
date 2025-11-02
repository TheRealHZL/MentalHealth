import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  AuthResponse,
  LoginRequest,
  RegisterPatientRequest,
  RegisterTherapistRequest,
  User,
  UpdateProfileRequest,
  ChangePasswordRequest,
  NotificationPreferences,
  PrivacySettings,
  MoodEntry,
  CreateMoodRequest,
  DreamEntry,
  CreateDreamRequest,
  DreamInterpretationRequest,
  MoodTrend,
  OverviewStats,
  WellnessScore,
  MoodPatterns,
  ActivityCorrelation,
  WeeklyInsight,
  MonthlyInsight,
  AIMoodAnalysis,
  AIChatRequest,
  AIChatResponse,
  TherapyNote,
  CreateTherapyNoteRequest,
  TherapyTechnique,
  TherapySession,
  CreateTherapySessionRequest,
  ShareKey,
  CreateShareKeyRequest,
  AccessLog,
  SharedDataStats,
  CalendarEvent,
  CreateCalendarEventRequest,
  PaginatedResponse
} from '@/types';
import { generateMockCalendarEvents } from './mockCalendarData';

// Use relative URL - Next.js will proxy to backend via rewrites
// In Docker: Next.js server (running in container) proxies to http://backend:8080
// Locally: Next.js dev server proxies to http://localhost:8080
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';
const BASE_URL = `/api/${API_VERSION}`;

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      withCredentials: true, // ✅ Send httpOnly cookies with requests
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - clear user data
          this.clearUserData();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // User Data Management (tokens stored in httpOnly cookies)
  private clearUserData(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('user');
    }
  }

  // Auth Endpoints
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/users/login', data);
    // Token stored in httpOnly cookie by backend - no localStorage needed!
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  }

  async registerPatient(data: RegisterPatientRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/users/register/patient', data);
    // Token stored in httpOnly cookie by backend - no localStorage needed!
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  }

  async registerTherapist(data: RegisterTherapistRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/users/register/therapist', data);
    // Token stored in httpOnly cookie by backend - no localStorage needed!
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  }

  async getProfile(): Promise<User> {
    const response = await this.client.get<User>('/users/profile');
    return response.data;
  }

  async updateProfile(data: Partial<User>): Promise<User> {
    const response = await this.client.put<User>('/users/profile', data);
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      // Call backend logout to clear httpOnly cookies
      await this.client.post('/users/logout');
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      // Clear user data and redirect
      this.clearUserData();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
  }

  // User Settings Endpoints
  async changePassword(data: ChangePasswordRequest): Promise<void> {
    await this.client.put('/users/change-password', data);
  }

  async uploadAvatar(file: File): Promise<User> {
    const formData = new FormData();
    formData.append('avatar', file);
    const response = await this.client.post<User>('/users/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    // Update local user data
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(response.data));
    }
    return response.data;
  }

  async getNotificationPreferences(): Promise<NotificationPreferences> {
    const response = await this.client.get<NotificationPreferences>('/users/notifications');
    return response.data;
  }

  async updateNotificationPreferences(data: NotificationPreferences): Promise<NotificationPreferences> {
    const response = await this.client.put<NotificationPreferences>('/users/notifications', data);
    return response.data;
  }

  async getPrivacySettings(): Promise<PrivacySettings> {
    const response = await this.client.get<PrivacySettings>('/users/privacy');
    return response.data;
  }

  async updatePrivacySettings(data: PrivacySettings): Promise<PrivacySettings> {
    const response = await this.client.put<PrivacySettings>('/users/privacy', data);
    return response.data;
  }

  // Mood Endpoints
  async createMoodEntry(data: CreateMoodRequest): Promise<MoodEntry> {
    const response = await this.client.post<MoodEntry>('/mood/', data);
    return response.data;
  }

  async getMoodEntries(page: number = 1, size: number = 10): Promise<PaginatedResponse<MoodEntry>> {
    const response = await this.client.get<PaginatedResponse<MoodEntry>>('/mood/', {
      params: { page, size }
    });
    return response.data;
  }

  async getMoodEntry(id: string): Promise<MoodEntry> {
    const response = await this.client.get<MoodEntry>(`/mood/${id}`);
    return response.data;
  }

  async updateMoodEntry(id: string, data: Partial<CreateMoodRequest>): Promise<MoodEntry> {
    const response = await this.client.put<MoodEntry>(`/mood/${id}`, data);
    return response.data;
  }

  async deleteMoodEntry(id: string): Promise<void> {
    await this.client.delete(`/mood/${id}`);
  }

  // Dream Endpoints
  async createDreamEntry(data: CreateDreamRequest): Promise<DreamEntry> {
    const response = await this.client.post<DreamEntry>('/dreams/', data);
    return response.data;
  }

  async getDreamEntries(page: number = 1, size: number = 10): Promise<PaginatedResponse<DreamEntry>> {
    const response = await this.client.get<PaginatedResponse<DreamEntry>>('/dreams/', {
      params: { page, size }
    });
    return response.data;
  }

  async interpretDream(data: DreamInterpretationRequest): Promise<{ interpretation: string }> {
    const response = await this.client.post<{ interpretation: string }>('/dreams/interpret', data);
    return response.data;
  }

  // Analytics Endpoints
  async getMoodTrends(days: number = 30): Promise<MoodTrend[]> {
    const response = await this.client.get<MoodTrend[]>('/analytics/mood/trends', {
      params: { days }
    });
    return response.data;
  }

  async getOverviewStats(): Promise<OverviewStats> {
    const response = await this.client.get<OverviewStats>('/analytics/overview');
    return response.data;
  }

  async getWellnessScore(): Promise<WellnessScore> {
    const response = await this.client.get<WellnessScore>('/analytics/wellness-score');
    return response.data;
  }

  async getMoodPatterns(): Promise<MoodPatterns> {
    const response = await this.client.get<MoodPatterns>('/analytics/mood/patterns');
    return response.data;
  }

  async getMoodCorrelations(): Promise<ActivityCorrelation[]> {
    const response = await this.client.get<ActivityCorrelation[]>('/analytics/mood/correlations');
    return response.data;
  }

  async getWeeklyInsights(): Promise<WeeklyInsight> {
    const response = await this.client.get<WeeklyInsight>('/analytics/insights/weekly');
    return response.data;
  }

  async getMonthlyInsights(): Promise<MonthlyInsight> {
    const response = await this.client.get<MonthlyInsight>('/analytics/insights/monthly');
    return response.data;
  }

  // AI Endpoints
  async analyzeMood(moodData: CreateMoodRequest): Promise<AIMoodAnalysis> {
    const response = await this.client.post<AIMoodAnalysis>('/ai/analyze-mood', moodData);
    return response.data;
  }

  async chatWithAI(data: AIChatRequest): Promise<AIChatResponse> {
    const response = await this.client.post<AIChatResponse>('/ai/chat', data);
    return response.data;
  }

  // Therapy Endpoints
  async createTherapyNote(data: CreateTherapyNoteRequest): Promise<TherapyNote> {
    const response = await this.client.post<TherapyNote>('/therapy/notes', data);
    return response.data;
  }

  async getTherapyNotes(page: number = 1, size: number = 10): Promise<PaginatedResponse<TherapyNote>> {
    const response = await this.client.get<PaginatedResponse<TherapyNote>>('/therapy/notes', {
      params: { page, size }
    });
    return response.data;
  }

  async getTherapyNote(id: string): Promise<TherapyNote> {
    const response = await this.client.get<TherapyNote>(`/therapy/notes/${id}`);
    return response.data;
  }

  async updateTherapyNote(id: string, data: Partial<CreateTherapyNoteRequest>): Promise<TherapyNote> {
    const response = await this.client.put<TherapyNote>(`/therapy/notes/${id}`, data);
    return response.data;
  }

  async deleteTherapyNote(id: string): Promise<void> {
    await this.client.delete(`/therapy/notes/${id}`);
  }

  async getTherapyTechniques(): Promise<TherapyTechnique[]> {
    const response = await this.client.get<TherapyTechnique[]>('/therapy/techniques');
    return response.data;
  }

  async createTherapySession(data: CreateTherapySessionRequest): Promise<TherapySession> {
    const response = await this.client.post<TherapySession>('/therapy/sessions', data);
    return response.data;
  }

  async getTherapySessions(page: number = 1, size: number = 10): Promise<PaginatedResponse<TherapySession>> {
    const response = await this.client.get<PaginatedResponse<TherapySession>>('/therapy/sessions', {
      params: { page, size }
    });
    return response.data;
  }

  async getTherapyProgress(): Promise<any> {
    const response = await this.client.get('/therapy/progress');
    return response.data;
  }

  // Data Sharing Endpoints
  async createShareKey(data: CreateShareKeyRequest): Promise<ShareKey> {
    const response = await this.client.post<ShareKey>('/sharing/keys', data);
    return response.data;
  }

  async getShareKeys(page: number = 1, size: number = 10): Promise<PaginatedResponse<ShareKey>> {
    const response = await this.client.get<PaginatedResponse<ShareKey>>('/sharing/keys', {
      params: { page, size }
    });
    return response.data;
  }

  async getShareKey(id: string): Promise<ShareKey> {
    const response = await this.client.get<ShareKey>(`/sharing/keys/${id}`);
    return response.data;
  }

  async revokeShareKey(id: string): Promise<void> {
    await this.client.delete(`/sharing/keys/${id}`);
  }

  async getAccessLogs(shareKeyId?: string, page: number = 1, size: number = 10): Promise<PaginatedResponse<AccessLog>> {
    const params: any = { page, size };
    if (shareKeyId) params.share_key_id = shareKeyId;
    const response = await this.client.get<PaginatedResponse<AccessLog>>('/sharing/access-logs', {
      params
    });
    return response.data;
  }

  async getSharedDataStats(): Promise<SharedDataStats> {
    const response = await this.client.get<SharedDataStats>('/sharing/stats');
    return response.data;
  }

  // Admin Endpoints
  async getAdminStats(): Promise<any> {
    const response = await this.client.get('/admin/stats');
    return response.data;
  }

  async getTrainingJobs(): Promise<PaginatedResponse<any>> {
    const response = await this.client.get('/ai/training/jobs');
    return response.data;
  }

  async startTraining(data: any): Promise<any> {
    const response = await this.client.post('/ai/training/start', data);
    return response.data;
  }

  async stopTraining(jobId: string): Promise<void> {
    await this.client.post(`/ai/training/jobs/${jobId}/stop`);
  }

  async getModels(): Promise<any> {
    const response = await this.client.get('/admin/models');
    return response.data;
  }

  async activateModel(modelId: string): Promise<any> {
    const response = await this.client.post(`/admin/models/${modelId}/activate`);
    return response.data;
  }

  async getDatasets(): Promise<any> {
    const response = await this.client.get('/admin/datasets');
    return response.data;
  }

  async uploadDataset(formData: FormData): Promise<any> {
    const response = await this.client.post('/admin/datasets', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
  }

  async getAllUsers(): Promise<any> {
    const response = await this.client.get('/admin/users');
    return response.data;
  }

  async updateUserRole(userId: string, role: string): Promise<any> {
    const response = await this.client.put(`/admin/users/${userId}/role`, { role });
    return response.data;
  }

  // Calendar/Planner Endpoints (with mock data fallback until backend is implemented)
  async getCalendarEvents(startDate?: string, endDate?: string): Promise<CalendarEvent[]> {
    try {
      const params: any = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;

      const response = await this.client.get<CalendarEvent[]>('/calendar/events', { params });
      return response.data;
    } catch (err) {
      // Fallback to mock data until backend is implemented
      console.warn('Calendar API not yet implemented, using mock data');
      return generateMockCalendarEvents();
    }
  }

  async getCalendarEvent(id: string): Promise<CalendarEvent> {
    try {
      const response = await this.client.get<CalendarEvent>(`/calendar/events/${id}`);
      return response.data;
    } catch (err) {
      // Fallback to mock data
      const mockEvents = generateMockCalendarEvents();
      const event = mockEvents.find(e => e.id === id);
      if (!event) throw new Error('Event not found');
      return event;
    }
  }

  async createCalendarEvent(data: CreateCalendarEventRequest): Promise<CalendarEvent> {
    try {
      const response = await this.client.post<CalendarEvent>('/calendar/events', data);
      return response.data;
    } catch (err) {
      // Fallback: Create mock event
      console.warn('Calendar API not yet implemented, creating mock event');
      const newEvent: CalendarEvent = {
        id: `event-${Date.now()}`,
        ...data,
        is_recurring: data.is_recurring || false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };

      // Store in localStorage for persistence
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('calendar_events');
        const events = stored ? JSON.parse(stored) : [];
        events.push(newEvent);
        localStorage.setItem('calendar_events', JSON.stringify(events));
      }

      return newEvent;
    }
  }

  async updateCalendarEvent(id: string, data: Partial<CreateCalendarEventRequest>): Promise<CalendarEvent> {
    try {
      const response = await this.client.put<CalendarEvent>(`/calendar/events/${id}`, data);
      return response.data;
    } catch (err) {
      // Fallback: Update mock event
      console.warn('Calendar API not yet implemented, updating mock event');
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('calendar_events');
        const events = stored ? JSON.parse(stored) : generateMockCalendarEvents();
        const index = events.findIndex((e: CalendarEvent) => e.id === id);
        if (index >= 0) {
          events[index] = { ...events[index], ...data, updated_at: new Date().toISOString() };
          localStorage.setItem('calendar_events', JSON.stringify(events));
          return events[index];
        }
      }
      throw new Error('Event not found');
    }
  }

  async deleteCalendarEvent(id: string): Promise<void> {
    try {
      await this.client.delete(`/calendar/events/${id}`);
    } catch (err) {
      // Fallback: Delete mock event
      console.warn('Calendar API not yet implemented, deleting mock event');
      if (typeof window !== 'undefined') {
        const stored = localStorage.getItem('calendar_events');
        const events = stored ? JSON.parse(stored) : [];
        const filtered = events.filter((e: CalendarEvent) => e.id !== id);
        localStorage.setItem('calendar_events', JSON.stringify(filtered));
      }
    }
  }

  // Helper to check if user is authenticated
  // Note: With httpOnly cookies, we check if user data exists in localStorage
  // The actual authentication is verified by backend via cookie
  isAuthenticated(): boolean {
    return !!this.getCurrentUser();
  }

  // Get current user from localStorage
  getCurrentUser(): User | null {
    if (typeof window === 'undefined') return null;
    const userStr = localStorage.getItem('user');
    if (!userStr) return null;
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
}

export const apiClient = new ApiClient();
export default apiClient;
