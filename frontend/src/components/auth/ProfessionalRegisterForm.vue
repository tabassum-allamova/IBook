<script setup lang="ts">
import { ref, reactive } from 'vue'
import api from '@/lib/axios'

const emit = defineEmits<{
  (e: 'success'): void
}>()

const form = reactive({
  fullName: '',
  email: '',
  password: '',
  role: 'BARBER' as 'BARBER' | 'SHOP_OWNER',
  phone: '',
})

const errors = reactive({
  fullName: '',
  email: '',
  password: '',
  role: '',
  phone: '',
  general: '',
})

const loading = ref(false)

function validateEmail(email: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)
}

function validatePassword(password: string) {
  return password.length >= 8 && /[a-zA-Z]/.test(password) && /[0-9]/.test(password)
}

function validate() {
  errors.fullName = ''
  errors.email = ''
  errors.password = ''
  errors.role = ''
  errors.phone = ''
  errors.general = ''
  let valid = true

  if (!form.fullName.trim()) {
    errors.fullName = 'Full name is required.'
    valid = false
  }

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
  } else if (!validatePassword(form.password)) {
    errors.password = 'Password must be at least 8 characters and include a letter and a number.'
    valid = false
  }

  if (!form.role) {
    errors.role = 'Please select a role.'
    valid = false
  }

  return valid
}

async function submit() {
  if (!validate()) return
  loading.value = true

  try {
    await api.post('/api/auth/register/professional/', {
      email: form.email,
      password: form.password,
      full_name: form.fullName,
      role: form.role,
      ...(form.phone ? { phone_number: form.phone } : {}),
    })
    emit('success')
  } catch (err: unknown) {
    const axiosErr = err as {
      response?: {
        data?: Record<string, string | string[]>
      }
    }
    const data = axiosErr.response?.data
    if (data) {
      if (data.email) errors.email = Array.isArray(data.email) ? data.email[0] : data.email
      if (data.password)
        errors.password = Array.isArray(data.password) ? data.password[0] : data.password
      if (data.full_name)
        errors.fullName = Array.isArray(data.full_name) ? data.full_name[0] : data.full_name
      if (data.phone_number)
        errors.phone = Array.isArray(data.phone_number) ? data.phone_number[0] : data.phone_number
      if (data.role) errors.role = Array.isArray(data.role) ? data.role[0] : data.role
      if (data.non_field_errors)
        errors.general = Array.isArray(data.non_field_errors)
          ? data.non_field_errors[0]
          : data.non_field_errors
      if (data.detail)
        errors.general = typeof data.detail === 'string' ? data.detail : (data.detail as string[])[0]
    } else {
      errors.general = 'Something went wrong. Please try again.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form @submit.prevent="submit" novalidate>
    <!-- Full Name -->
    <div class="mb-5">
      <label for="fullName" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
        Full Name
      </label>
      <input
        id="fullName"
        v-model="form.fullName"
        type="text"
        autocomplete="name"
        placeholder="John Smith"
        class="w-full px-4 py-3 rounded-lg border text-ibook-brown-900 placeholder-ibook-brown-300 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.fullName
            ? 'border-red-400 focus:ring-red-300'
            : 'border-ibook-brown-200 focus:ring-ibook-brown-400 focus:border-ibook-brown-400'
        "
      />
      <p v-if="errors.fullName" class="mt-1.5 text-sm text-red-600">{{ errors.fullName }}</p>
    </div>

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
    <div class="mb-5">
      <label for="password" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
        Password
      </label>
      <input
        id="password"
        v-model="form.password"
        type="password"
        autocomplete="new-password"
        placeholder="••••••••"
        class="w-full px-4 py-3 rounded-lg border text-ibook-brown-900 placeholder-ibook-brown-300 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.password
            ? 'border-red-400 focus:ring-red-300'
            : 'border-ibook-brown-200 focus:ring-ibook-brown-400 focus:border-ibook-brown-400'
        "
      />
      <p v-if="errors.password" class="mt-1.5 text-sm text-red-600">{{ errors.password }}</p>
      <p v-else class="mt-1 text-xs text-ibook-brown-400">
        Must be 8+ characters with at least one letter and one number.
      </p>
    </div>

    <!-- Role selector -->
    <div class="mb-5">
      <label class="block text-sm font-semibold text-ibook-brown-700 mb-2">
        I am a…
      </label>
      <div class="grid grid-cols-2 gap-3">
        <label
          class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 cursor-pointer transition-colors"
          :class="
            form.role === 'BARBER'
              ? 'border-ibook-brown-600 bg-ibook-brown-50 text-ibook-brown-800'
              : 'border-ibook-brown-200 text-ibook-brown-500 hover:border-ibook-brown-400'
          "
        >
          <input type="radio" v-model="form.role" value="BARBER" class="sr-only" />
          <span class="font-medium text-sm">Barber</span>
        </label>
        <label
          class="flex items-center justify-center gap-2 px-4 py-3 rounded-lg border-2 cursor-pointer transition-colors"
          :class="
            form.role === 'SHOP_OWNER'
              ? 'border-ibook-brown-600 bg-ibook-brown-50 text-ibook-brown-800'
              : 'border-ibook-brown-200 text-ibook-brown-500 hover:border-ibook-brown-400'
          "
        >
          <input type="radio" v-model="form.role" value="SHOP_OWNER" class="sr-only" />
          <span class="font-medium text-sm">Shop Owner</span>
        </label>
      </div>
      <p v-if="errors.role" class="mt-1.5 text-sm text-red-600">{{ errors.role }}</p>
    </div>

    <!-- Phone (optional) -->
    <div class="mb-6">
      <label for="phone" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
        Phone
        <span class="font-normal text-ibook-brown-400">(optional)</span>
      </label>
      <input
        id="phone"
        v-model="form.phone"
        type="tel"
        autocomplete="tel"
        placeholder="+1 555 000 0000"
        class="w-full px-4 py-3 rounded-lg border border-ibook-brown-200 text-ibook-brown-900 placeholder-ibook-brown-300 bg-white focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:border-ibook-brown-400 transition-colors"
      />
      <p v-if="errors.phone" class="mt-1.5 text-sm text-red-600">{{ errors.phone }}</p>
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
      <span v-if="loading">Creating account…</span>
      <span v-else>Create Account</span>
    </button>
  </form>
</template>
