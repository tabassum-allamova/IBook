<script setup lang="ts">
import { ref, reactive, computed, watch, onBeforeUnmount } from 'vue'
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import api from '@/lib/axios'
import { useAuthStore } from '@/stores/auth'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'

const toast = useToast()
const { t } = useI18n()

interface ProfileData {
  id: number
  email: string
  full_name: string
  phone_number?: string
  avatar?: string
  role: string
  bio?: string
  years_of_experience?: number
}

const auth = useAuthStore()
const queryClient = useQueryClient()

const { data: profile, isLoading, isError } = useQuery<ProfileData>({
  queryKey: ['profile'],
  queryFn: async () => {
    const res = await api.get<ProfileData>('/api/auth/profile/')
    return res.data
  },
})

const form = reactive({
  fullName: '',
  phone: '',
  bio: '',
  yearsOfExperience: '' as string | number,
})

const errors = reactive({
  fullName: '',
  phone: '',
  bio: '',
  yearsOfExperience: '',
  avatar: '',
  general: '',
})

function resetErrors() {
  errors.fullName = ''
  errors.phone = ''
  errors.bio = ''
  errors.yearsOfExperience = ''
  errors.avatar = ''
  errors.general = ''
}

const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string | null>(null)
const fileInputRef = ref<HTMLInputElement | null>(null)

const avatarSrc = computed(() => avatarPreview.value ?? profile.value?.avatar ?? null)

const successMsg = ref('')

watch(
  profile,
  (p) => {
    if (p) {
      form.fullName = p.full_name ?? ''
      form.phone = p.phone_number ?? ''
      form.bio = p.bio ?? ''
      form.yearsOfExperience = p.years_of_experience ?? ''
    }
  },
  { immediate: true },
)

function openFilePicker() {
  fileInputRef.value?.click()
}

function onFileChange(e: Event) {
  const target = e.target as HTMLInputElement
  const file = target.files?.[0] ?? null
  if (!file) return
  if (!file.type.startsWith('image/')) {
    toast.error('Please select an image file.')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    toast.error('Image is too large (max 5 MB).')
    return
  }
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value)
  avatarFile.value = file
  avatarPreview.value = URL.createObjectURL(file)
}

function clearPendingAvatar() {
  avatarFile.value = null
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value)
  avatarPreview.value = null
  if (fileInputRef.value) fileInputRef.value.value = ''
}

onBeforeUnmount(() => {
  if (avatarPreview.value) URL.revokeObjectURL(avatarPreview.value)
})

function validate(): boolean {
  resetErrors()
  let ok = true

  const trimmedName = form.fullName.trim()
  if (!trimmedName) {
    errors.fullName = 'Please enter your full name.'
    ok = false
  } else if (trimmedName.length < 2) {
    errors.fullName = 'Name is too short.'
    ok = false
  } else if (trimmedName.length > 80) {
    errors.fullName = 'Name is too long (max 80 characters).'
    ok = false
  }

  const phone = form.phone.trim()
  if (phone) {
    if (phone.length > 20) {
      errors.phone = 'Phone number is too long (max 20 characters).'
      ok = false
    } else if (!/^\+?[\d\s()\-]+$/.test(phone)) {
      errors.phone = 'Phone can only contain digits, spaces, +, -, and parentheses.'
      ok = false
    } else {
      const digits = phone.replace(/\D/g, '')
      if (digits.length < 7) {
        errors.phone = 'Please enter a valid phone number (at least 7 digits).'
        ok = false
      } else if (digits.length > 15) {
        errors.phone = 'Phone number is too long (max 15 digits).'
        ok = false
      }
    }
  }

  if (auth.user?.role === 'BARBER') {
    if (form.bio && form.bio.length > 500) {
      errors.bio = 'Bio is too long (max 500 characters).'
      ok = false
    }
    if (form.yearsOfExperience !== '') {
      const n = Number(form.yearsOfExperience)
      if (!Number.isFinite(n) || n < 0 || n > 60) {
        errors.yearsOfExperience = 'Enter a number between 0 and 60.'
        ok = false
      }
    }
  }

  return ok
}

function applyBackendErrors(data: unknown) {
  if (!data || typeof data !== 'object') {
    errors.general = 'Something went wrong. Please try again.'
    return
  }
  const body = data as Record<string, unknown>
  const firstString = (v: unknown): string => {
    if (typeof v === 'string') return v
    if (Array.isArray(v) && typeof v[0] === 'string') return v[0]
    return ''
  }

  // Map backend field names → our form fields.
  const firstNameErr = firstString(body.first_name)
  const lastNameErr = firstString(body.last_name)
  if (firstNameErr || lastNameErr) errors.fullName = firstNameErr || lastNameErr
  const phoneErr = firstString(body.phone_number)
  if (phoneErr) errors.phone = phoneErr
  const bioErr = firstString(body.bio)
  if (bioErr) errors.bio = bioErr
  const yoeErr = firstString(body.years_of_experience)
  if (yoeErr) errors.yearsOfExperience = yoeErr
  const avatarErr = firstString(body.avatar)
  if (avatarErr) errors.avatar = avatarErr

  const anyFieldError =
    errors.fullName || errors.phone || errors.bio || errors.yearsOfExperience || errors.avatar
  if (!anyFieldError) {
    errors.general =
      firstString(body.detail) ||
      firstString(body.non_field_errors) ||
      'Failed to update profile. Please try again.'
  }
}

const { mutate: saveProfile, isPending: isSaving } = useMutation({
  mutationFn: async () => {
    const nameParts = form.fullName.trim().split(/\s+/)
    const first_name = nameParts.shift() ?? ''
    const last_name = nameParts.join(' ')
    const isBarber = auth.user?.role === 'BARBER'
    const phoneValue = form.phone.trim() // CharField(blank=True) — empty string, never null

    if (avatarFile.value) {
      const fd = new FormData()
      fd.append('first_name', first_name)
      fd.append('last_name', last_name)
      fd.append('phone_number', phoneValue)
      if (isBarber) {
        fd.append('bio', form.bio ?? '')
        if (form.yearsOfExperience !== '') {
          fd.append('years_of_experience', String(form.yearsOfExperience))
        }
      }
      fd.append('avatar', avatarFile.value)
      const res = await api.patch<ProfileData>('/api/auth/profile/', fd)
      return res.data
    }

    const payload: Record<string, unknown> = {
      first_name,
      last_name,
      phone_number: phoneValue,
    }
    if (isBarber) {
      payload.bio = form.bio ?? ''
      payload.years_of_experience = form.yearsOfExperience !== '' ? Number(form.yearsOfExperience) : null
    }
    const res = await api.patch<ProfileData>('/api/auth/profile/', payload)
    return res.data
  },
  onSuccess: (data) => {
    queryClient.setQueryData(['profile'], data)
    if (auth.user) {
      auth.setAuth({
        user: { ...auth.user, fullName: data.full_name },
        accessToken: auth.accessToken ?? '',
      })
    }
    clearPendingAvatar()
    resetErrors()
    successMsg.value = t('settings.saved')
    toast.success(t('settings.saved'))
    setTimeout(() => {
      successMsg.value = ''
    }, 4000)
  },
  onError: (err: unknown) => {
    successMsg.value = ''
    const axiosErr = err as { response?: { data?: unknown } }
    applyBackendErrors(axiosErr.response?.data)
  },
})

function roleLabel(role: string) {
  switch (role) {
    case 'CUSTOMER':
      return t('settings.roles.customer')
    case 'BARBER':
      return t('settings.roles.barber')
    case 'SHOP_OWNER':
      return t('settings.roles.shopOwner')
    default:
      return role
  }
}

function submit() {
  if (!validate()) return
  saveProfile()
}
</script>

<template>
  <section class="max-w-6xl mx-auto">
    <!-- Header -->
    <div class="mb-6 md:mb-8 flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
      <div>
        <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
          {{ t('settings.title') }}
        </h1>
        <p class="mt-1 text-sm text-slate-600">{{ t('settings.subtitle') }}</p>
      </div>
      <RouterLink
        v-if="auth.user?.role === 'BARBER' && profile?.id"
        :to="{ name: 'customer-barber-profile', params: { barberId: profile.id } }"
        target="_blank"
        rel="noopener"
        class="inline-flex items-center gap-1.5 h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors self-start sm:self-auto"
      >
        {{ t('settings.viewPublicPage') }}
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M14 3h7v7m0-7L10 14M5 10v11h11" />
        </svg>
      </RouterLink>
    </div>

    <!-- Loading skeleton -->
    <div v-if="isLoading" class="space-y-4">
      <SkeletonBlock height="2.5rem" />
      <SkeletonBlock height="2.5rem" />
      <SkeletonBlock height="2.5rem" />
    </div>

    <!-- Error -->
    <div
      v-else-if="isError"
      class="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
    >
      {{ t('settings.loadError') }}
    </div>

    <!-- Form -->
    <form
      v-else
      novalidate
      class="max-w-2xl bg-white rounded-xl border border-slate-200 p-6 md:p-8 space-y-5"
      @submit.prevent="submit"
    >
      <!-- Role -->
      <div class="flex items-center gap-2">
        <span
          class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-medium bg-slate-100 text-slate-700"
        >
          <span class="h-1.5 w-1.5 rounded-full bg-slate-500"></span>
          {{ roleLabel(profile?.role ?? '') }}
        </span>
      </div>

      <!-- Avatar uploader -->
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-2">
          {{ t('settings.profilePhoto') }}
        </label>
        <div class="flex items-center gap-4">
          <div class="flex-shrink-0 h-20 w-20 rounded-full overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center">
            <img
              v-if="avatarSrc"
              :src="avatarSrc"
              :alt="profile?.full_name ?? 'Profile photo'"
              class="w-full h-full object-cover"
            />
            <svg
              v-else
              class="h-9 w-9 text-slate-300"
              fill="none"
              stroke="currentColor"
              stroke-width="1.4"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <div class="flex flex-col items-start gap-1.5">
            <div class="flex items-center gap-2">
              <button
                type="button"
                class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
                @click="openFilePicker"
              >
                {{ avatarFile ? t('settings.chooseAnother') : t('settings.uploadPhoto') }}
              </button>
              <button
                v-if="avatarFile"
                type="button"
                class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors"
                @click="clearPendingAvatar"
              >
                {{ t('common.cancel') }}
              </button>
            </div>
            <p class="text-sm text-slate-500">{{ t('settings.photoHint') }}</p>
          </div>
          <input
            ref="fileInputRef"
            type="file"
            accept="image/png,image/jpeg,image/webp"
            class="hidden"
            @change="onFileChange"
          />
        </div>
      </div>

      <!-- Full Name -->
      <div>
        <label for="fullName" class="block text-sm font-medium text-slate-700 mb-1.5">
          {{ t('settings.fullName') }}
        </label>
        <input
          id="fullName"
          v-model="form.fullName"
          type="text"
          autocomplete="name"
          class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
          :class="
            errors.fullName
              ? 'border-red-400 focus:ring-red-200'
              : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
          "
        />
        <p v-if="errors.fullName" class="mt-1.5 text-sm text-red-600">{{ errors.fullName }}</p>
      </div>

      <!-- Email (readonly) -->
      <div>
        <label for="email" class="block text-sm font-medium text-slate-700 mb-1.5">
          {{ t('auth.register.email') }}
          <span class="font-normal text-slate-400">{{ t('settings.emailReadonly') }}</span>
        </label>
        <input
          id="email"
          :value="profile?.email ?? ''"
          type="email"
          readonly
          class="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 text-[15px] text-slate-500 bg-slate-50 cursor-not-allowed"
        />
      </div>

      <!-- Phone -->
      <div>
        <label for="phone" class="block text-sm font-medium text-slate-700 mb-1.5">
          {{ t('auth.register.phone') }}
          <span class="font-normal text-slate-400">{{ t('settings.phoneOptional') }}</span>
        </label>
        <input
          id="phone"
          v-model="form.phone"
          type="tel"
          autocomplete="tel"
          :placeholder="t('settings.phonePlaceholder')"
          class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
          :class="
            errors.phone
              ? 'border-red-400 focus:ring-red-200'
              : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
          "
        />
        <p v-if="errors.phone" class="mt-1.5 text-sm text-red-600">{{ errors.phone }}</p>
      </div>

      <!-- Barber-only fields -->
      <template v-if="auth.user?.role === 'BARBER'">
        <div>
          <label for="bio" class="block text-sm font-medium text-slate-700 mb-1.5">
            {{ t('settings.bio') }}
            <span class="font-normal text-slate-400">{{ t('settings.phoneOptional') }}</span>
          </label>
          <textarea
            id="bio"
            v-model="form.bio"
            rows="4"
            :placeholder="t('settings.bioPlaceholder')"
            class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors resize-none"
            :class="
              errors.bio
                ? 'border-red-400 focus:ring-red-200'
                : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
            "
          ></textarea>
          <p v-if="errors.bio" class="mt-1.5 text-sm text-red-600">{{ errors.bio }}</p>
        </div>

        <div>
          <label for="experience" class="block text-sm font-medium text-slate-700 mb-1.5">
            {{ t('settings.yearsOfExperience') }}
            <span class="font-normal text-slate-400">{{ t('settings.phoneOptional') }}</span>
          </label>
          <input
            id="experience"
            v-model="form.yearsOfExperience"
            type="number"
            min="0"
            max="60"
            placeholder="0"
            class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
            :class="
              errors.yearsOfExperience
                ? 'border-red-400 focus:ring-red-200'
                : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'
            "
          />
          <p v-if="errors.yearsOfExperience" class="mt-1.5 text-sm text-red-600">
            {{ errors.yearsOfExperience }}
          </p>
        </div>
      </template>

      <!-- Success -->
      <div
        v-if="successMsg"
        class="px-4 py-3 bg-emerald-50 border border-emerald-200 rounded-lg text-sm text-emerald-700"
      >
        {{ successMsg }}
      </div>

      <!-- General / avatar error -->
      <div
        v-if="errors.general || errors.avatar"
        class="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
      >
        {{ errors.general || errors.avatar }}
      </div>

      <!-- Save -->
      <div class="pt-2">
        <button
          type="submit"
          :disabled="isSaving"
          class="inline-flex items-center justify-center gap-2 h-11 px-6 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed"
        >
          <template v-if="isSaving">
            <svg class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
              <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
            </svg>
            {{ t('settings.saving') }}
          </template>
          <template v-else>
            {{ t('settings.save') }}
          </template>
        </button>
      </div>
    </form>
  </section>
</template>
