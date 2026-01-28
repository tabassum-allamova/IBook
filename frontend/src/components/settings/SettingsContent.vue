<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import api from '@/lib/axios'
import { useAuthStore } from '@/stores/auth'

interface ProfileData {
  id: number
  email: string
  full_name: string
  phone_number?: string
  avatar_url?: string
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
  avatarUrl: '',
  bio: '',
  yearsOfExperience: '' as string | number,
})

const successMsg = ref('')
const errorMsg = ref('')

// Populate form when profile loads
watch(profile, (p) => {
  if (p) {
    form.fullName = p.full_name ?? ''
    form.phone = p.phone_number ?? ''
    form.avatarUrl = p.avatar_url ?? ''
    form.bio = p.bio ?? ''
    form.yearsOfExperience = p.years_of_experience ?? ''
  }
})

const { mutate: saveProfile, isPending: isSaving } = useMutation({
  mutationFn: async () => {
    const payload: Record<string, unknown> = {
      full_name: form.fullName,
    }
    if (form.phone !== undefined) payload.phone_number = form.phone || null
    if (form.avatarUrl !== undefined) payload.avatar_url = form.avatarUrl || null

    const isBarber = auth.user?.role === 'BARBER'
    if (isBarber) {
      payload.bio = form.bio || null
      payload.years_of_experience = form.yearsOfExperience !== '' ? Number(form.yearsOfExperience) : null
    }

    const res = await api.patch<ProfileData>('/api/auth/profile/', payload)
    return res.data
  },
  onSuccess: (data) => {
    queryClient.setQueryData(['profile'], data)
    // Update auth store with new name
    if (auth.user) {
      auth.setAuth({
        user: { ...auth.user, fullName: data.full_name },
        accessToken: auth.accessToken ?? '',
      })
    }
    successMsg.value = 'Profile updated successfully.'
    errorMsg.value = ''
    setTimeout(() => { successMsg.value = '' }, 4000)
  },
  onError: () => {
    errorMsg.value = 'Failed to update profile. Please try again.'
    successMsg.value = ''
  },
})

function roleBadgeClass(role: string) {
  switch (role) {
    case 'CUSTOMER':
      return 'bg-ibook-brown-100 text-ibook-brown-700'
    case 'BARBER':
      return 'bg-ibook-gold-400 text-white'
    case 'SHOP_OWNER':
      return 'bg-ibook-brown-800 text-white'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function roleLabel(role: string) {
  switch (role) {
    case 'CUSTOMER':
      return 'Customer'
    case 'BARBER':
      return 'Barber'
    case 'SHOP_OWNER':
      return 'Shop Owner'
    default:
      return role
  }
}

function submit() {
  saveProfile()
}
</script>

<template>
  <div class="p-8 max-w-2xl">
    <!-- Header -->
    <div class="mb-8">
      <h1 class="text-3xl font-bold text-ibook-brown-900">Settings</h1>
      <p class="mt-1 text-ibook-brown-500">Manage your account information.</p>
    </div>

    <!-- Loading -->
    <div v-if="isLoading" class="flex items-center gap-3 text-ibook-brown-500">
      <svg class="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
      </svg>
      Loading profile…
    </div>

    <!-- Error loading -->
    <div
      v-else-if="isError"
      class="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
    >
      Failed to load profile. Please refresh the page.
    </div>

    <!-- Form -->
    <form v-else @submit.prevent="submit" novalidate>
      <!-- Role badge -->
      <div class="mb-6 flex items-center gap-3">
        <span
          class="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold tracking-wide"
          :class="roleBadgeClass(profile?.role ?? '')"
        >
          {{ roleLabel(profile?.role ?? '') }}
        </span>
      </div>

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
          class="w-full px-4 py-3 rounded-lg border border-ibook-brown-200 text-ibook-brown-900 bg-white focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:border-ibook-brown-400 transition-colors"
        />
      </div>

      <!-- Email (readonly) -->
      <div class="mb-5">
        <label for="email" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
          Email
          <span class="font-normal text-ibook-brown-400">(cannot be changed)</span>
        </label>
        <input
          id="email"
          :value="profile?.email ?? ''"
          type="email"
          readonly
          class="w-full px-4 py-3 rounded-lg border border-ibook-brown-100 text-ibook-brown-500 bg-ibook-brown-50 cursor-not-allowed"
        />
      </div>

      <!-- Phone (optional) -->
      <div class="mb-5">
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
          class="w-full px-4 py-3 rounded-lg border border-ibook-brown-200 text-ibook-brown-900 bg-white focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:border-ibook-brown-400 transition-colors"
        />
      </div>

      <!-- Avatar URL (optional) -->
      <div class="mb-5">
        <label for="avatarUrl" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
          Avatar URL
          <span class="font-normal text-ibook-brown-400">(optional)</span>
        </label>
        <input
          id="avatarUrl"
          v-model="form.avatarUrl"
          type="url"
          placeholder="https://example.com/avatar.jpg"
          class="w-full px-4 py-3 rounded-lg border border-ibook-brown-200 text-ibook-brown-900 bg-white focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:border-ibook-brown-400 transition-colors"
        />
      </div>

      <!-- Barber-only fields -->
      <template v-if="auth.user?.role === 'BARBER'">
        <div class="mb-5">
          <label for="bio" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
            Bio
            <span class="font-normal text-ibook-brown-400">(optional)</span>
          </label>
          <textarea
            id="bio"
            v-model="form.bio"
            rows="4"
            placeholder="Tell clients about yourself and your specialties…"
            class="w-full px-4 py-3 rounded-lg border border-ibook-brown-200 text-ibook-brown-900 bg-white focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:border-ibook-brown-400 transition-colors resize-none"
          ></textarea>
        </div>

        <div class="mb-6">
          <label for="experience" class="block text-sm font-semibold text-ibook-brown-700 mb-1.5">
            Years of Experience
            <span class="font-normal text-ibook-brown-400">(optional)</span>
          </label>
          <input
            id="experience"
            v-model="form.yearsOfExperience"
            type="number"
            min="0"
            max="60"
            placeholder="0"
            class="w-full px-4 py-3 rounded-lg border border-ibook-brown-200 text-ibook-brown-900 bg-white focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:border-ibook-brown-400 transition-colors"
          />
        </div>
      </template>

      <!-- Success message -->
      <div
        v-if="successMsg"
        class="mb-5 px-4 py-3 bg-green-50 border border-green-200 rounded-lg text-sm text-green-700"
      >
        {{ successMsg }}
      </div>

      <!-- Error message -->
      <div
        v-if="errorMsg"
        class="mb-5 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
      >
        {{ errorMsg }}
      </div>

      <!-- Save button -->
      <button
        type="submit"
        :disabled="isSaving"
        class="py-3 px-8 bg-ibook-brown-700 hover:bg-ibook-brown-600 text-white font-semibold rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:ring-offset-2 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
      >
        <span v-if="isSaving">Saving…</span>
        <span v-else>Save Changes</span>
      </button>
    </form>
  </div>
</template>
