<script setup lang="ts">
import { useRouter, RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import api from '@/lib/axios'
import LanguageSwitcher from '@/components/ui/LanguageSwitcher.vue'

defineProps<{
  navItems: Array<{ label: string; to: string }>
}>()

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
    router.push('/login')
  }
}
</script>

<template>
  <aside class="w-64 h-full bg-white border-r border-slate-200 flex flex-col shrink-0">
    <!-- Logo + user -->
    <div class="px-5 py-5 border-b border-slate-200">
      <div class="flex items-center gap-2">
        <span class="inline-flex items-center justify-center h-8 w-8 rounded-md bg-slate-900 text-white text-sm font-bold">i</span>
        <span class="text-lg font-semibold text-slate-900 tracking-tight">IBook</span>
      </div>
      <p class="mt-3 text-sm text-slate-500 truncate" :title="auth.user?.fullName">
        {{ auth.user?.fullName }}
      </p>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 px-3 py-4 space-y-1">
      <RouterLink
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors"
        active-class="!bg-slate-100 !text-slate-900"
      >
        {{ item.label }}
      </RouterLink>
    </nav>

    <!-- Footer: language + logout -->
    <div class="px-3 py-4 border-t border-slate-200 space-y-2">
      <div class="px-1">
        <LanguageSwitcher />
      </div>
      <button
        type="button"
        class="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
        @click="logout"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
        </svg>
        {{ t('common.signOut') }}
      </button>
    </div>
  </aside>
</template>
