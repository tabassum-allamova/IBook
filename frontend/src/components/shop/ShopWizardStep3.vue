<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{
  modelValue: File[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: File[]]
}>()

const MAX_PHOTOS = 5
const fileInputRef = ref<HTMLInputElement | null>(null)

function openFilePicker() {
  fileInputRef.value?.click()
}

function onFilesSelected(event: Event) {
  const input = event.target as HTMLInputElement
  if (!input.files) return

  const newFiles = Array.from(input.files)
  const combined = [...props.modelValue, ...newFiles].slice(0, MAX_PHOTOS)
  emit('update:modelValue', combined)

  // Reset input so same file can be re-selected
  input.value = ''
}

function removePhoto(index: number) {
  const updated = props.modelValue.filter((_, i) => i !== index)
  emit('update:modelValue', updated)
}

function previewUrl(file: File): string {
  return URL.createObjectURL(file)
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-ibook-brown-700 mb-1">Shop Photos</h2>
      <p class="text-sm text-ibook-brown-400">Upload up to {{ MAX_PHOTOS }} photos of your shop</p>
    </div>

    <!-- Hidden file input -->
    <input
      ref="fileInputRef"
      type="file"
      accept="image/*"
      multiple
      class="hidden"
      @change="onFilesSelected"
    />

    <!-- Add Photos Button -->
    <div class="flex items-center gap-3">
      <button
        type="button"
        @click="openFilePicker"
        :disabled="modelValue.length >= MAX_PHOTOS"
        class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        :class="
          modelValue.length >= MAX_PHOTOS
            ? 'bg-ibook-brown-100 text-ibook-brown-400 cursor-not-allowed'
            : 'bg-ibook-gold-500 hover:bg-ibook-gold-600 text-white cursor-pointer'
        "
      >
        Add Photos
      </button>
      <span v-if="modelValue.length >= MAX_PHOTOS" class="text-sm text-ibook-brown-400">
        {{ MAX_PHOTOS }}/{{ MAX_PHOTOS }} maximum
      </span>
      <span v-else class="text-sm text-ibook-brown-400">
        {{ modelValue.length }}/{{ MAX_PHOTOS }} selected
      </span>
    </div>

    <!-- Photo Previews -->
    <div v-if="modelValue.length > 0" class="flex flex-wrap gap-3">
      <div
        v-for="(file, index) in modelValue"
        :key="index"
        class="relative group"
      >
        <img
          :src="previewUrl(file)"
          :alt="`Photo ${index + 1}`"
          class="w-20 h-20 object-cover rounded-lg border border-ibook-brown-200"
        />
        <button
          type="button"
          @click="removePhoto(index)"
          class="absolute -top-2 -right-2 w-5 h-5 bg-red-500 hover:bg-red-600 text-white rounded-full text-xs flex items-center justify-center font-bold transition-colors shadow"
          aria-label="Remove photo"
        >
          ×
        </button>
      </div>
    </div>

    <!-- Empty state -->
    <div
      v-else
      class="flex flex-col items-center justify-center py-10 border-2 border-dashed border-ibook-brown-200 rounded-lg text-ibook-brown-400"
    >
      <p class="text-sm">No photos selected yet</p>
      <p class="text-xs mt-1">Photos help customers find and recognize your shop</p>
    </div>
  </div>
</template>
