import axios from 'axios'
import Cookies from 'js-cookie'
import type { useAuthStore } from '@/stores/auth'

type AuthStore = ReturnType<typeof useAuthStore>

// Lazily injected to avoid circular dep (store imports nothing; axios is imported by store indirectly)
let _store: AuthStore | null = null

export function initAxiosStore(getStore: () => AuthStore) {
  // Call getter once pinia is ready
  _store = getStore()
}

const api = axios.create({
  baseURL: '/',
  withCredentials: true, // send httpOnly refresh_token cookie
})

// Shared refresh promise to deduplicate concurrent refresh calls
let refreshPromise: Promise<string> | null = null

async function doRefresh(): Promise<string> {
  if (refreshPromise) return refreshPromise

  refreshPromise = axios
    .post<{ access: string }>(
      '/api/auth/token/refresh/',
      {},
      { withCredentials: true },
    )
    .then((res) => {
      const newToken = res.data.access
      if (_store) {
        // Update token in store directly (triggers the watcher for persistence)
        _store.accessToken = newToken
      }
      Cookies.set('access_token', newToken, { sameSite: 'strict' })
      return newToken
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

// Request interceptor: attach Bearer token
api.interceptors.request.use((config) => {
  const token = _store?.accessToken
  if (token) {
    config.headers = config.headers ?? {}
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

// Response interceptor: handle 401 → refresh → retry
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as typeof error.config & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const newToken = await doRefresh()
        originalRequest.headers = originalRequest.headers ?? {}
        originalRequest.headers['Authorization'] = `Bearer ${newToken}`
        return api(originalRequest)
      } catch {
        // Refresh failed — clear auth and redirect to login
        if (_store) {
          _store.clearAuth()
        }
        Cookies.remove('access_token')
        window.location.href = '/login'
        return Promise.reject(error)
      }
    }

    return Promise.reject(error)
  },
)

export default api
