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

  // Set by clearAuth so the persistence watcher doesn't write a partial
  // `{ user: null, accessToken: '<old token>' }` snapshot in the gap
  // between setting the two refs to null.
  let isClearing = false

  function clearAuth() {
    isClearing = true
    // Remove first so a concurrent watcher run or another tab sees the
    // empty state immediately, before either ref is mutated.
    localStorage.removeItem(STORAGE_KEY)
    user.value = null
    accessToken.value = null
    isClearing = false
  }

  // Keep storage in sync when values change externally (e.g., token refresh)
  watch([user, accessToken], () => {
    if (isClearing) return
    if (user.value && accessToken.value) {
      persist()
    } else if (!user.value && !accessToken.value) {
      // Both nulled out — ensure storage matches.
      localStorage.removeItem(STORAGE_KEY)
    }
    // Deliberately no write for the mixed / partial case; treat it as
    // transient and wait for the next tick to settle.
  })

  return {
    user,
    accessToken,
    isAuthenticated,
    setAuth,
    clearAuth,
  }
})
