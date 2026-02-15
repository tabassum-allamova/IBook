<script setup lang="ts">
import { ref } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import BarberLayout from '@/layouts/BarberLayout.vue'
import api from '@/lib/axios'

interface ProfileData {
  id: number
  email: string
  full_name: string
  avatar: string | null
}

const queryClient = useQueryClient()

const { data: profile, isLoading } = useQuery<ProfileData>({
  queryKey: ['profile'],
  queryFn: async () => {
    const res = await api.get<ProfileData>('/api/auth/profile/')
    return res.data
  },
})

const fileInput = ref<HTMLInputElement | null>(null)
const previewUrl = ref<string | null>(null)
const selectedFile = ref<File | null>(null)
const successMessage = ref('')
const errorMessage = ref('')

function getAvatarUrl(avatar: string | null): string {
  if (previewUrl.value) return previewUrl.value
  if (!avatar) return ''
  if (avatar.startsWith('http')) return avatar
  return `/${avatar.replace(/^\//, '')}`
}

function onChangePhotoClick() {
  fileInput.value?.click()
}

function onFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return
  selectedFile.value = file
  previewUrl.value = URL.createObjectURL(file)
  successMessage.value = ''
  errorMessage.value = ''
}

const uploadMutation = useMutation({
  mutationFn: async (file: File) => {
    const formData = new FormData()
    formData.append('avatar', file)
    const res = await api.patch<ProfileData>('/api/auth/profile/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return res.data
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['profile'] })
    selectedFile.value = null
    successMessage.value = 'Photo updated successfully'
    errorMessage.value = ''
  },
  onError: () => {
    errorMessage.value = 'Failed to upload photo. Please try again.'
  },
})

async function onSavePhoto() {
  if (!selectedFile.value) return
  await uploadMutation.mutateAsync(selectedFile.value)
}
</script>

<template>
  <BarberLayout>
    <div class="p-8">
      <!-- Page header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-ibook-brown-900">Profile Setup</h1>
        <p class="mt-1 text-ibook-brown-500">Manage your public profile photo.</p>
      </div>

      <!-- Profile card -->
      <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-8 max-w-md">
        <div v-if="isLoading" class="text-ibook-brown-400 text-sm">Loading profile...</div>
        <div v-else class="flex flex-col items-center gap-6">
          <!-- Avatar preview -->
          <div class="relative">
            <div
              class="w-24 h-24 rounded-full border-2 border-ibook-brown-200 overflow-hidden bg-ibook-brown-100 flex items-center justify-center"
            >
              <img
                v-if="previewUrl || profile?.avatar"
                :src="getAvatarUrl(profile?.avatar ?? null)"
                alt="Profile photo"
                class="w-full h-full object-cover"
              />
              <span v-else class="text-ibook-brown-400 text-3xl font-bold">
                {{ profile?.full_name?.charAt(0)?.toUpperCase() ?? '?' }}
              </span>
            </div>
          </div>

          <!-- Upload actions -->
          <div class="flex flex-col items-center gap-3 w-full">
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onFileSelect"
            />
            <button
              type="button"
              class="px-5 py-2 rounded-lg border border-ibook-brown-200 text-ibook-brown-700 text-sm font-medium hover:bg-ibook-brown-50 transition-colors cursor-pointer"
              @click="onChangePhotoClick"
            >
              Change Photo
            </button>
            <button
              v-if="selectedFile"
              type="button"
              :disabled="uploadMutation.isPending.value"
              class="px-5 py-2 rounded-lg bg-ibook-gold-500 text-white text-sm font-semibold hover:bg-ibook-gold-600 transition-colors disabled:opacity-60 cursor-pointer"
              @click="onSavePhoto"
            >
              {{ uploadMutation.isPending.value ? 'Saving...' : 'Save Photo' }}
            </button>
          </div>

          <!-- Feedback messages -->
          <p v-if="successMessage" class="text-sm text-green-600 font-medium">
            {{ successMessage }}
          </p>
          <p v-if="errorMessage" class="text-sm text-red-600 font-medium">{{ errorMessage }}</p>

          <!-- User info -->
          <div class="w-full border-t border-ibook-brown-100 pt-4 space-y-2">
            <div class="flex justify-between text-sm">
              <span class="text-ibook-brown-500">Name</span>
              <span class="text-ibook-brown-800 font-medium">{{ profile?.full_name }}</span>
            </div>
            <div class="flex justify-between text-sm">
              <span class="text-ibook-brown-500">Email</span>
              <span class="text-ibook-brown-800 font-medium">{{ profile?.email }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </BarberLayout>
</template>
