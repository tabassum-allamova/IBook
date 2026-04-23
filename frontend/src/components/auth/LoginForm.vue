<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import api from '@/lib/axios'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/stores/auth'
import { roleDashboard } from '@/router'

const { t } = useI18n()
const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  email: '',
  password: '',
})

const errors = reactive({
  email: '',
  password: '',
  general: '',
})

const loading = ref(false)

function validateEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function validate() {
  errors.email = ''
  errors.password = ''
  errors.general = ''
  let valid = true

  if (!form.email) {
    errors.email = t('auth.login.errors.emailRequired')
    valid = false
  } else if (!validateEmail(form.email)) {
    errors.email = t('auth.login.errors.emailInvalid')
    valid = false
  }

  if (!form.password) {
    errors.password = t('auth.login.errors.passwordRequired')
    valid = false
  }

  return valid
}

async function submit() {
  if (!validate()) return
  loading.value = true
  errors.general = ''

  try {
    const res = await api.post<{
      access: string
      user: { id: number; email: string; role: UserRole; full_name: string }
    }>('/api/auth/login/', {
      email: form.email,
      password: form.password,
    })

    const { access, user } = res.data

    auth.setAuth({
      accessToken: access,
      user: {
        id: user.id,
        email: user.email,
        role: user.role,
        fullName: user.full_name,
      },
    })

    const returnUrl = (router.currentRoute.value.query.returnUrl as string) || ''
    const destination = returnUrl || roleDashboard(user.role)
    router.push(destination)
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string; non_field_errors?: string[] } } }
    const detail = axiosErr.response?.data?.detail
    const nonField = axiosErr.response?.data?.non_field_errors?.[0]
    errors.general = detail || nonField || t('auth.login.errors.invalid')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form @submit.prevent="submit" novalidate class="space-y-5">
    <!-- Email -->
    <div>
      <label for="email" class="block text-sm font-medium text-slate-700 mb-1.5">
        {{ t('auth.login.email') }}
      </label>
      <input
        id="email"
        v-model="form.email"
        type="email"
        autocomplete="email"
        placeholder="you@example.com"
        class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.email
            ? 'border-red-400 focus:ring-red-200'
            : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
        "
      />
      <p v-if="errors.email" class="mt-1.5 text-sm text-red-600">{{ errors.email }}</p>
    </div>

    <!-- Password -->
    <div>
      <label for="password" class="block text-sm font-medium text-slate-700 mb-1.5">
        {{ t('auth.login.password') }}
      </label>
      <input
        id="password"
        v-model="form.password"
        type="password"
        autocomplete="current-password"
        placeholder="••••••••"
        class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.password
            ? 'border-red-400 focus:ring-red-200'
            : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
        "
      />
      <p v-if="errors.password" class="mt-1.5 text-sm text-red-600">{{ errors.password }}</p>
    </div>

    <!-- General error -->
    <div
      v-if="errors.general"
      class="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
    >
      {{ errors.general }}
    </div>

    <!-- Submit -->
    <button
      type="submit"
      :disabled="loading"
      class="w-full inline-flex items-center justify-center gap-2 h-11 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
    >
      <template v-if="loading">
        <svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
          <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
        </svg>
        {{ t('common.loading') }}
      </template>
      <template v-else>
        {{ t('auth.login.submit') }}
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </template>
    </button>
  </form>
</template>
