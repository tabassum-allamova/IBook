<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '@/lib/axios'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

type Status = 'verifying' | 'success' | 'failed'

const status = ref<Status>('verifying')
const errorMessage = ref('')

onMounted(async () => {
  const token = route.query.token
  if (typeof token !== 'string' || token === '') {
    status.value = 'failed'
    errorMessage.value = t('verifyEmail.failed')
    return
  }

  try {
    await api.get('/api/auth/verify-email/', { params: { token } })
    status.value = 'success'
    // Brief pause so the user sees the success state before being sent on.
    setTimeout(() => {
      router.push({ path: '/login', query: { verified: 'true' } })
    }, 1500)
  } catch (err: unknown) {
    status.value = 'failed'
    const detail = (err as { response?: { data?: { detail?: string } } })
      .response?.data?.detail
    errorMessage.value = detail || t('verifyEmail.failed')
  }
})
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col">
    <header class="border-b border-slate-200">
      <div class="max-w-7xl mx-auto flex items-center justify-between px-5 md:px-8 lg:px-12 h-16">
        <RouterLink
          to="/customer/explore"
          class="text-lg font-bold text-slate-900 tracking-tight"
        >
          IBook
        </RouterLink>
      </div>
    </header>

    <main class="flex-1 flex items-start justify-center px-5 md:px-8 pt-16 md:pt-24 pb-16">
      <div class="w-full max-w-md text-center">
        <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
          {{ t('verifyEmail.title') }}
        </h1>

        <!-- Verifying -->
        <div v-if="status === 'verifying'" class="mt-8 inline-flex items-center gap-2.5 text-sm text-slate-600">
          <svg class="h-4 w-4 animate-spin text-slate-500" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
            <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
          </svg>
          {{ t('verifyEmail.verifying') }}
        </div>

        <!-- Success -->
        <div v-else-if="status === 'success'" class="mt-8 space-y-5">
          <div class="inline-flex items-center justify-center h-12 w-12 rounded-full bg-emerald-50 text-emerald-600">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p class="text-[15px] text-slate-700">{{ t('verifyEmail.success') }}</p>
        </div>

        <!-- Failed -->
        <div v-else class="mt-8 space-y-5">
          <div class="inline-flex items-center justify-center h-12 w-12 rounded-full bg-red-50 text-red-600">
            <svg class="h-6 w-6" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
          <p class="text-[15px] text-slate-700">{{ errorMessage }}</p>
          <RouterLink
            to="/login"
            class="inline-flex items-center justify-center gap-1.5 h-10 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
          >
            {{ t('verifyEmail.backToLogin') }}
          </RouterLink>
        </div>
      </div>
    </main>
  </div>
</template>
