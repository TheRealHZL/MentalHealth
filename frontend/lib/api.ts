import axios, { AxiosInstance, AxiosError } from 'axios';
import type { 
  AuthResponse, 
  LoginRequest, 
  RegisterPatientRequest, 
  RegisterTherapistRequest,
  User,
  MoodEntry,
  CreateMoodRequest,
  DreamEntry,
  CreateDreamRequest,
  DreamInterpretationRequest,
  MoodTrend,
  OverviewStats,
  WellnessScore,
  AIMoodAnalysis,
  AIChatRequest,
  AIChatResponse,
  PaginatedResponse
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';
const API_VERSION = process.env.NEXT_PUBLIC_API_VERSION || 'v1';
const BASE_URL = `${API_URL}/api/${API_VERSION}`;

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

  // AI Endpoints
  async analyzeMood(moodData: CreateMoodRequest): Promise<AIMoodAnalysis> {
    const response = await this.client.post<AIMoodAnalysis>('/ai/analyze-mood', moodData);
    return response.data;
  }

  async chatWithAI(data: AIChatRequest): Promise<AIChatResponse> {
    const response = await this.client.post<AIChatResponse>('/ai/chat', data);
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
