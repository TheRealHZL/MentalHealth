import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuthStore } from '@/stores/authStore';

export function useAuth() {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, setUser, logout, checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  const requireAuth = () => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  };

  const requireRole = (role: 'patient' | 'therapist') => {
    if (!isLoading && (!isAuthenticated || user?.role !== role)) {
      router.push('/login');
    }
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    setUser,
    logout,
    requireAuth,
    requireRole,
  };
}
