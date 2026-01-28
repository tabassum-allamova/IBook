<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/lib/axios'
import { useAuthStore } from '@/stores/auth'
import type { UserRole } from '@/stores/auth'
import { roleDashboard } from '@/router'
import Cookies from 'js-cookie'

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
    errors.email = 'Email is required.'
    valid = false
  } else if (!validateEmail(form.email)) {
    errors.email = 'Please enter a valid email address.'
    valid = false
  }

  if (!form.password) {
    errors.password = 'Password is required.'
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

    Cookies.set('access_token', access, { sameSite: 'strict' })

    const returnUrl = (router.currentRoute.value.query.returnUrl as string) || ''
    const destination = returnUrl || roleDashboard(user.role)
    router.push(destination)
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string; non_field_errors?: string[] } } }
    const detail = axiosErr.response?.data?.detail
    const nonField = axiosErr.response?.data?.non_field_errors?.[0]
    errors.general = detail || nonField || 'Invalid email or password. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form @submit.prevent="submit" novalidate>
    <!-- Email -->
    <div class="mb-5">
      <label for="email" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
        Email
      </label>
      <input
        id="email"
        v-model="form.email"
        type="email"
        autocomplete="email"
        placeholder="you@example.com"
        class="w-full px-4 py-3 rounded-lg border text-ibook-brown-900 placeholder-ibook-brown-300 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.email
            ? 'border-red-400 focus:ring-red-300'
            : 'border-ibook-brown-200 focus:ring-ibook-brown-400 focus:border-ibook-brown-400'
        "
      />
      <p v-if="errors.email" class="mt-1.5 text-sm text-red-600">{{ errors.email }}</p>
    </div>

    <!-- Password -->
    <div class="mb-6">
      <label for="password" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
        Password
      </label>
      <input
        id="password"
        v-model="form.password"
        type="password"
        autocomplete="current-password"
        placeholder="••••••••"
        class="w-full px-4 py-3 rounded-lg border text-ibook-brown-900 placeholder-ibook-brown-300 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.password
            ? 'border-red-400 focus:ring-red-300'
            : 'border-ibook-brown-200 focus:ring-ibook-brown-400 focus:border-ibook-brown-400'
        "
      />
      <p v-if="errors.password" class="mt-1.5 text-sm text-red-600">{{ errors.password }}</p>
    </div>

    <!-- General error -->
    <div
      v-if="errors.general"
      class="mb-5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
    >
      {{ errors.general }}
    </div>

    <!-- Submit -->
    <button
      type="submit"
      :disabled="loading"
      class="w-full py-3 px-6 bg-ibook-brown-700 hover:bg-ibook-brown-600 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
    >
      <span v-if="loading">Signing in…</span>
      <span v-else>Sign In</span>
    </button>
  </form>
</template>
