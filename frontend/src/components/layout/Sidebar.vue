<script setup lang="ts">
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/lib/axios'
import Cookies from 'js-cookie'

defineProps<{
  navItems: Array<{ label: string; to: string }>
}>()

const router = useRouter()
const auth = useAuthStore()

async function logout() {
  try {
    await api.post('/api/auth/logout/')
  } catch {
    // ignore errors — always clear local auth
  } finally {
    auth.clearAuth()
    Cookies.remove('access_token')
    router.push('/login')
  }
}
</script>

<template>
  <aside class="w-64 min-h-screen bg-ibook-brown-900 text-white flex flex-col shadow-xl">
    <!-- Logo -->
    <div class="px-6 py-6 border-b border-ibook-brown-700">
      <span class="text-2xl font-black tracking-tight text-ibook-gold-400">IBook</span>
      <p class="text-ibook-brown-400 text-xs mt-1">{{ auth.user?.fullName }}</p>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-4 py-6 space-y-1">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-4 py-3 rounded-lg text-ibook-brown-300 hover:bg-ibook-brown-700 hover:text-white transition-colors text-sm font-medium"
        active-class="bg-ibook-brown-700 text-white"
      >
        {{ item.label }}
      </RouterLink>
    </nav>

    <!-- Logout -->
    <div class="px-4 py-6 border-t border-ibook-brown-700">
      <button
        @click="logout"
        class="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-ibook-brown-400 hover:bg-ibook-brown-700 hover:text-white transition-colors text-sm font-medium cursor-pointer"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
          />
        </svg>
        Logout
      </button>
    </div>
  </aside>
</template>
