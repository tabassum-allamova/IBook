<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useI18n } from 'vue-i18n'
import api from '@/lib/axios'

const { t } = useI18n()

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
    errors.fullName = t('auth.register.errors.fullNameRequired')
    valid = false
  }

  if (!form.email) {
    errors.email = t('auth.register.errors.emailRequired')
    valid = false
  } else if (!validateEmail(form.email)) {
    errors.email = t('auth.register.errors.emailInvalid')
    valid = false
  }

  if (!form.password) {
    errors.password = t('auth.register.errors.passwordRequired')
    valid = false
  } else if (!validatePassword(form.password)) {
    errors.password = t('auth.register.errors.passwordStrength')
    valid = false
  }

  if (!form.role) {
    errors.role = t('auth.register.errors.roleRequired')
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
    const axiosErr = err as { response?: { data?: Record<string, string | string[]> } }
    const data = axiosErr.response?.data
    const first = (v: unknown) =>
      typeof v === 'string' ? v : Array.isArray(v) && typeof v[0] === 'string' ? v[0] : ''
    if (data) {
      errors.email = first(data.email) || ''
      errors.password = first(data.password) || ''
      errors.fullName = first(data.full_name) || ''
      errors.phone = first(data.phone_number) || ''
      errors.role = first(data.role) || ''
      errors.general = first(data.non_field_errors) || first(data.detail) || ''
    } else {
      errors.general = t('auth.register.errors.generic')
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <form @submit.prevent="submit" novalidate class="space-y-5">
    <!-- Full name -->
    <div>
      <label for="pro-fullName" class="block text-sm font-medium text-slate-700 mb-1.5">
        {{ t('auth.register.fullName') }}
      </label>
      <input
        id="pro-fullName"
        v-model="form.fullName"
        type="text"
        autocomplete="name"
        :placeholder="t('auth.register.fullNamePlaceholder')"
        class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.fullName
            ? 'border-red-400 focus:ring-red-200'
            : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
        "
      />
      <p v-if="errors.fullName" class="mt-1.5 text-sm text-red-600">{{ errors.fullName }}</p>
    </div>

    <!-- Email -->
    <div>
      <label for="pro-email" class="block text-sm font-medium text-slate-700 mb-1.5">
        {{ t('auth.register.email') }}
      </label>
      <input
        id="pro-email"
        v-model="form.email"
        type="email"
        autocomplete="email"
        :placeholder="t('auth.register.emailPlaceholder')"
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
      <label for="pro-password" class="block text-sm font-medium text-slate-700 mb-1.5">
        {{ t('auth.register.password') }}
      </label>
      <input
        id="pro-password"
        v-model="form.password"
        type="password"
        autocomplete="new-password"
        placeholder="••••••••"
        class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.password
            ? 'border-red-400 focus:ring-red-200'
            : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
        "
      />
      <p v-if="errors.password" class="mt-1.5 text-sm text-red-600">{{ errors.password }}</p>
      <p v-else class="mt-1.5 text-sm text-slate-500">
        {{ t('auth.register.passwordHint') }}
      </p>
    </div>

    <!-- Role -->
    <div>
      <label class="block text-sm font-medium text-slate-700 mb-2">
        {{ t('auth.register.iAmA') }}
      </label>
      <div class="grid grid-cols-2 gap-3">
        <label
          class="flex items-center justify-center gap-2 h-11 px-3 rounded-lg border cursor-pointer transition-colors bg-white"
          :class="
            form.role === 'BARBER'
              ? 'border-slate-900 ring-2 ring-slate-900/10 text-slate-900'
              : 'border-slate-200 text-slate-600 hover:border-slate-400'
          "
        >
          <input type="radio" v-model="form.role" value="BARBER" class="sr-only" />
          <span class="text-sm font-medium">{{ t('auth.register.barber') }}</span>
        </label>
        <label
          class="flex items-center justify-center gap-2 h-11 px-3 rounded-lg border cursor-pointer transition-colors bg-white"
          :class="
            form.role === 'SHOP_OWNER'
              ? 'border-slate-900 ring-2 ring-slate-900/10 text-slate-900'
              : 'border-slate-200 text-slate-600 hover:border-slate-400'
          "
        >
          <input type="radio" v-model="form.role" value="SHOP_OWNER" class="sr-only" />
          <span class="text-sm font-medium">{{ t('auth.register.shopOwner') }}</span>
        </label>
      </div>
      <p v-if="errors.role" class="mt-1.5 text-sm text-red-600">{{ errors.role }}</p>
    </div>

    <!-- Phone -->
    <div>
      <label for="pro-phone" class="block text-sm font-medium text-slate-700 mb-1.5">
        {{ t('auth.register.phone') }}
        <span class="font-normal text-slate-400">{{ t('auth.register.phoneOptional') }}</span>
      </label>
      <input
        id="pro-phone"
        v-model="form.phone"
        type="tel"
        autocomplete="tel"
        :placeholder="t('auth.register.phonePlaceholder')"
        class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
        :class="
          errors.phone
            ? 'border-red-400 focus:ring-red-200'
            : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
        "
      />
      <p v-if="errors.phone" class="mt-1.5 text-sm text-red-600">{{ errors.phone }}</p>
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
        {{ t('auth.register.submitting') }}
      </template>
      <template v-else>
        {{ t('auth.register.submit') }}
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </template>
    </button>
  </form>
</template>
