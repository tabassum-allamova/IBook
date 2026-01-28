import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'

export type UserRole = 'CUSTOMER' | 'BARBER' | 'SHOP_OWNER'

export interface AuthUser {
  id: number
  email: string
  role: UserRole
  fullName: string
}

const STORAGE_KEY = 'ibook_auth'

function loadFromStorage(): { user: AuthUser | null; accessToken: string | null } {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { user: null, accessToken: null }
    return JSON.parse(raw)
  } catch {
    return { user: null, accessToken: null }
  }
}

export const useAuthStore = defineStore('auth', () => {
  const saved = loadFromStorage()

  const user = ref<AuthUser | null>(saved.user)
  const accessToken = ref<string | null>(saved.accessToken)

  const isAuthenticated = computed(() => !!user.value && !!accessToken.value)

  function persist() {
    localStorage.setItem(
      STORAGE_KEY,
      JSON.stringify({ user: user.value, accessToken: accessToken.value }),
    )
  }

  function setAuth(payload: { user: AuthUser; accessToken: string }) {
    user.value = payload.user
    accessToken.value = payload.accessToken
    persist()
  }

  function clearAuth() {
    user.value = null
    accessToken.value = null
    localStorage.removeItem(STORAGE_KEY)
  }

  // Keep storage in sync when values change externally (e.g., token refresh)
  watch([user, accessToken], () => {
    if (user.value || accessToken.value) {
      persist()
    }
  })

  return {
    user,
    accessToken,
    isAuthenticated,
    setAuth,
    clearAuth,
  }
})
