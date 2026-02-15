<script setup lang="ts">
import { ref, watch } from 'vue'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import api from '@/lib/axios'

export interface Service {
  id: number
  name: string
  price: number
  duration_minutes: number
  sort_order: number
}

const props = defineProps<{
  mode: 'add' | 'edit'
  service?: Service
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

const queryClient = useQueryClient()

const durationOptions = [15, 30, 45, 60, 75, 90]

const name = ref('')
const price = ref<number | null>(null)
const duration = ref(30)
const errorMessage = ref('')

// Populate form in edit mode
watch(
  () => props.service,
  (svc) => {
    if (svc && props.mode === 'edit') {
      name.value = svc.name
      price.value = svc.price
      duration.value = svc.duration_minutes
    }
  },
  { immediate: true },
)

function closeModal() {
  emit('close')
}

function onBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) closeModal()
}

const saveMutation = useMutation({
  mutationFn: async () => {
    const payload = {
      name: name.value,
      price: price.value,
      duration_minutes: duration.value,
    }
    if (props.mode === 'add') {
      await api.post('/api/services/', payload)
    } else {
      await api.patch(`/api/services/${props.service!.id}/`, payload)
    }
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['services'] })
    emit('saved')
  },
  onError: () => {
    errorMessage.value = 'Failed to save service. Please try again.'
  },
})

const deleteMutation = useMutation({
  mutationFn: async () => {
    await api.delete(`/api/services/${props.service!.id}/`)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['services'] })
    emit('saved')
  },
  onError: () => {
    errorMessage.value = 'Failed to delete service. Please try again.'
  },
})

async function onSubmit() {
  if (!name.value.trim()) {
    errorMessage.value = 'Service name is required.'
    return
  }
  if (!price.value || price.value <= 0) {
    errorMessage.value = 'Valid price is required.'
    return
  }
  errorMessage.value = ''
  await saveMutation.mutateAsync()
}

async function onDelete() {
  if (!confirm('Delete this service?')) return
  await deleteMutation.mutateAsync()
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      @click="onBackdropClick"
    >
      <div
        class="bg-white rounded-2xl p-6 w-full max-w-md mx-4 shadow-2xl"
        @click.stop
      >
        <div class="flex items-center justify-between mb-6">
          <h2 class="text-xl font-bold text-ibook-brown-900">
            {{ mode === 'add' ? 'Add Service' : 'Edit Service' }}
          </h2>
          <button
            type="button"
            class="text-ibook-brown-400 hover:text-ibook-brown-700 transition-colors cursor-pointer"
            @click="closeModal"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form class="space-y-4" @submit.prevent="onSubmit">
          <!-- Name -->
          <div>
            <label class="block text-sm font-medium text-ibook-brown-700 mb-1">Service Name</label>
            <input
              v-model="name"
              type="text"
              required
              placeholder="e.g. Haircut"
              class="w-full rounded-lg border border-ibook-brown-200 px-3 py-2 text-ibook-brown-900 text-sm focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
            />
          </div>

          <!-- Price -->
          <div>
            <label class="block text-sm font-medium text-ibook-brown-700 mb-1">Price</label>
            <div class="relative">
              <input
                v-model.number="price"
                type="number"
                required
                min="0"
                step="100"
                placeholder="50000"
                class="w-full rounded-lg border border-ibook-brown-200 px-3 py-2 pr-14 text-ibook-brown-900 text-sm focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
              />
              <span class="absolute right-3 top-1/2 -translate-y-1/2 text-ibook-brown-400 text-sm font-medium pointer-events-none">
                UZS
              </span>
            </div>
          </div>

          <!-- Duration -->
          <div>
            <label class="block text-sm font-medium text-ibook-brown-700 mb-1">Duration</label>
            <select
              v-model.number="duration"
              class="w-full rounded-lg border border-ibook-brown-200 px-3 py-2 text-ibook-brown-900 text-sm focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
            >
              <option v-for="d in durationOptions" :key="d" :value="d">{{ d }} min</option>
            </select>
          </div>

          <!-- Error -->
          <p v-if="errorMessage" class="text-sm text-red-600">{{ errorMessage }}</p>

          <!-- Actions -->
          <div class="flex gap-3 pt-2">
            <button
              type="button"
              class="flex-1 px-4 py-2 rounded-lg border border-ibook-brown-200 text-ibook-brown-700 text-sm font-medium hover:bg-ibook-brown-50 transition-colors cursor-pointer"
              @click="closeModal"
            >
              Cancel
            </button>
            <button
              type="submit"
              :disabled="saveMutation.isPending.value"
              class="flex-1 px-4 py-2 rounded-lg bg-ibook-gold-500 text-white text-sm font-semibold hover:bg-ibook-gold-600 transition-colors disabled:opacity-60 cursor-pointer"
            >
              {{ saveMutation.isPending.value ? 'Saving...' : 'Save Service' }}
            </button>
          </div>

          <!-- Delete button in edit mode -->
          <div v-if="mode === 'edit'" class="pt-2 border-t border-ibook-brown-100">
            <button
              type="button"
              :disabled="deleteMutation.isPending.value"
              class="w-full px-4 py-2 rounded-lg border border-red-200 text-red-600 text-sm font-medium hover:bg-red-50 transition-colors disabled:opacity-60 cursor-pointer"
              @click="onDelete"
            >
              {{ deleteMutation.isPending.value ? 'Deleting...' : 'Delete Service' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </Teleport>
</template>
