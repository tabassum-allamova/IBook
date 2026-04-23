<script setup lang="ts">
import { useRouter, RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import api from '@/lib/axios'
import LanguageSwitcher from '@/components/ui/LanguageSwitcher.vue'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

async function logout() {
  try {
    await api.post('/api/auth/logout/')
  } catch {
    // ignore errors — always clear local auth
  } finally {
    auth.clearAuth()
    router.push('/customer/explore')
  }
}
</script>

<template>
  <header class="bg-white border-b border-slate-200 sticky top-0 z-40">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <RouterLink
          to="/customer/explore"
          class="flex items-center gap-2 text-slate-900 hover:text-slate-700 transition-colors"
        >
          <span class="inline-flex items-center justify-center h-8 w-8 rounded-md bg-slate-900 text-white text-sm font-bold">i</span>
          <span class="text-lg font-semibold tracking-tight">IBook</span>
        </RouterLink>

        <!-- Nav links (authenticated customers only) -->
        <nav
          v-if="auth.isAuthenticated && auth.user?.role === 'CUSTOMER'"
          class="hidden md:flex items-center gap-8"
        >
          <RouterLink
            to="/customer/explore"
            class="text-slate-600 hover:text-slate-900 transition-colors text-sm font-medium"
            active-class="!text-slate-900"
          >
            {{ t('nav.explore') }}
          </RouterLink>
          <RouterLink
            to="/customer/appointments"
            class="text-slate-600 hover:text-slate-900 transition-colors text-sm font-medium"
            active-class="!text-slate-900"
          >
            {{ t('nav.appointments') }}
          </RouterLink>
          <RouterLink
            to="/customer/settings"
            class="text-slate-600 hover:text-slate-900 transition-colors text-sm font-medium"
            active-class="!text-slate-900"
          >
            {{ t('nav.settings') }}
          </RouterLink>
        </nav>

        <!-- User area -->
        <div class="flex items-center gap-3">
          <LanguageSwitcher />
          <template v-if="auth.isAuthenticated">
            <span class="text-slate-600 text-sm hidden sm:block">
              {{ auth.user?.fullName }}
            </span>
            <button
              @click="logout"
              class="text-slate-600 hover:text-slate-900 text-sm font-medium px-3 py-2 transition-colors cursor-pointer"
            >
              {{ t('common.signOut') }}
            </button>
          </template>
          <template v-else>
            <RouterLink
              to="/login"
              class="text-slate-600 hover:text-slate-900 text-sm font-medium px-3 py-2 transition-colors hidden sm:inline-block"
            >
              {{ t('nav.login') }}
            </RouterLink>
            <RouterLink
              to="/register/customer"
              class="bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold px-4 py-2 rounded-lg transition-colors"
            >
              {{ t('nav.register') }}
            </RouterLink>
          </template>
        </div>
      </div>
    </div>
  </header>
</template>
