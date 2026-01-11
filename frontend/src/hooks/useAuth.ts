import { useAuthStore } from '@/stores/authStore'

export function useAuth() {
  const { user, accessToken, setAuth, clearAuth } = useAuthStore()
  const isAuthenticated = !!user && !!accessToken
  return { user, accessToken, isAuthenticated, setAuth, clearAuth }
}
