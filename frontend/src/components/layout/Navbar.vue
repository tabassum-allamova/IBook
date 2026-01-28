<script setup lang="ts">
import { useRouter, RouterLink } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import api from '@/lib/axios'
import Cookies from 'js-cookie'

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
  <header class="bg-ibook-brown-800 text-white shadow-md">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <RouterLink
          to="/customer/explore"
          class="text-2xl font-black tracking-tight text-ibook-gold-400 hover:text-ibook-gold-500 transition-colors"
        >
          IBook
        </RouterLink>

        <!-- Nav links -->
        <nav class="flex items-center gap-6">
          <RouterLink
            to="/customer/explore"
            class="text-ibook-brown-200 hover:text-white transition-colors text-sm font-medium"
            active-class="text-white"
          >
            Explore
          </RouterLink>
          <RouterLink
            to="/customer/appointments"
            class="text-ibook-brown-200 hover:text-white transition-colors text-sm font-medium"
            active-class="text-white"
          >
            Appointments
          </RouterLink>
          <RouterLink
            to="/customer/settings"
            class="text-ibook-brown-200 hover:text-white transition-colors text-sm font-medium"
            active-class="text-white"
          >
            Settings
          </RouterLink>
        </nav>

        <!-- User area -->
        <div class="flex items-center gap-4">
          <span class="text-ibook-brown-300 text-sm hidden sm:block">
            {{ auth.user?.fullName }}
          </span>
          <button
            @click="logout"
            class="bg-ibook-brown-600 hover:bg-ibook-brown-500 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors cursor-pointer"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  </header>
</template>
