import axios from 'axios'
import { useAuthStore } from '@/stores/authStore'

export const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  withCredentials: true, // sends httpOnly refresh cookie
})

// Attach access token to every request from Zustand store
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Refresh lock — prevents multiple concurrent refresh calls (Pitfall 4 fix)
let refreshPromise: Promise<string> | null = null

// Handle 401 — try silent refresh, then retry original request once
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true

      try {
        // Deduplicate concurrent 401s with a shared refresh promise lock
        if (!refreshPromise) {
          refreshPromise = axios
            .post<{ access: string }>(
              `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/token/refresh/`,
              {},
              { withCredentials: true }
            )
            .then((res) => res.data.access)
            .finally(() => {
              refreshPromise = null
            })
        }

        const newAccessToken = await refreshPromise

        // Update store with new access token
        const { user } = useAuthStore.getState()
        if (user) {
          useAuthStore.getState().setAuth(user, newAccessToken)
        }

        // Retry original request with new token
        original.headers.Authorization = `Bearer ${newAccessToken}`
        return api(original)
      } catch {
        // Refresh failed — clear auth and redirect to login
        useAuthStore.getState().clearAuth()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
    }
    return Promise.reject(error)
  }
)
