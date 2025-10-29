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

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
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
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          this.clearToken();
          if (typeof window !== 'undefined') {
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  // Token Management
  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('token');
  }

  private setToken(token: string): void {
    if (typeof window !== 'undefined') {
      localStorage.setItem('token', token);
    }
  }

  private clearToken(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    }
  }

  // Auth Endpoints
  async login(data: LoginRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/users/login', data);
    this.setToken(response.data.access_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  }

  async registerPatient(data: RegisterPatientRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/users/register/patient', data);
    this.setToken(response.data.access_token);
    if (typeof window !== 'undefined') {
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  }

  async registerTherapist(data: RegisterTherapistRequest): Promise<AuthResponse> {
    const response = await this.client.post<AuthResponse>('/users/register/therapist', data);
    this.setToken(response.data.access_token);
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

  logout(): void {
    this.clearToken();
    if (typeof window !== 'undefined') {
      window.location.href = '/login';
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

  // Helper to check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getToken();
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
