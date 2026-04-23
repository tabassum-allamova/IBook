<script setup lang="ts">
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useMutation, useQueryClient } from '@tanstack/vue-query'
import api from '@/lib/axios'

const { t } = useI18n()

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
  deleted: []
}>()

const queryClient = useQueryClient()

const durationOptions = [15, 30, 45, 60, 75, 90]

const form = reactive({
  name: '',
  price: null as number | null,
  duration: 30,
})
const errors = reactive({ name: '', price: '', general: '' })
const showConfirmDelete = ref(false)

function resetErrors() {
  errors.name = ''
  errors.price = ''
  errors.general = ''
}

watch(
  () => props.service,
  (svc) => {
    if (svc && props.mode === 'edit') {
      form.name = svc.name
      form.price = svc.price
      form.duration = svc.duration_minutes
    } else {
      form.name = ''
      form.price = null
      form.duration = 30
    }
  },
  { immediate: true },
)

function closeModal() {
  if (saveMutation.isPending.value || deleteMutation.isPending.value) return
  emit('close')
}

function onBackdropClick(event: MouseEvent) {
  if (event.target === event.currentTarget) closeModal()
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    if (showConfirmDelete.value) {
      showConfirmDelete.value = false
    } else {
      closeModal()
    }
  }
}

onMounted(() => {
  document.body.style.overflow = 'hidden'
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
})

function validate(): boolean {
  resetErrors()
  let ok = true
  if (!form.name.trim()) {
    errors.name = t('services.errors.nameRequired')
    ok = false
  } else if (form.name.length > 60) {
    errors.name = t('services.errors.nameRequired')
    ok = false
  }
  if (form.price === null || form.price <= 0) {
    errors.price = t('services.errors.priceRequired')
    ok = false
  } else if (form.price > 10_000_000) {
    errors.price = t('services.errors.priceInvalid')
    ok = false
  }
  return ok
}

const saveMutation = useMutation({
  mutationFn: async () => {
    const payload = {
      name: form.name.trim(),
      price: form.price,
      duration_minutes: form.duration,
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
  onError: (err: unknown) => {
    const body = (err as { response?: { data?: Record<string, unknown> } }).response?.data
    const first = (v: unknown) =>
      typeof v === 'string' ? v : Array.isArray(v) && typeof v[0] === 'string' ? v[0] : ''
    errors.name = first(body?.name) || errors.name
    errors.price = first(body?.price) || errors.price
    if (!errors.name && !errors.price) {
      errors.general = first(body?.detail) || t('toasts.genericError')
    }
  },
})

const deleteMutation = useMutation({
  mutationFn: async () => {
    await api.delete(`/api/services/${props.service!.id}/`)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['services'] })
    emit('deleted')
  },
  onError: () => {
    errors.general = 'Failed to delete service.'
  },
})

function onSubmit() {
  if (!validate()) return
  saveMutation.mutate()
}
</script>

<template>
  <Teleport to="body">
    <div
      class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-end md:items-center justify-center md:p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="service-modal-title"
      @click="onBackdropClick"
    >
      <div
        class="relative w-full md:max-w-md bg-white rounded-t-2xl md:rounded-2xl shadow-xl"
        @click.stop
      >
        <!-- Header -->
        <div class="flex items-start justify-between gap-4 px-5 md:px-6 py-4 border-b border-slate-200">
          <h2 id="service-modal-title" class="text-lg font-semibold text-slate-900 tracking-tight">
            {{ mode === 'add' ? t('services.addTitle') : t('services.editTitle') }}
          </h2>
          <button
            type="button"
            :aria-label="t('common.close')"
            class="flex-shrink-0 h-9 w-9 inline-flex items-center justify-center rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors disabled:opacity-50"
            :disabled="saveMutation.isPending.value || deleteMutation.isPending.value"
            @click="closeModal"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form class="p-5 md:p-6 space-y-5" novalidate @submit.prevent="onSubmit">
          <!-- Name -->
          <div>
            <label for="svc-name" class="block text-sm font-medium text-slate-700 mb-1.5">
              {{ t('services.name') }}
            </label>
            <input
              id="svc-name"
              v-model="form.name"
              type="text"
              :placeholder="t('services.namePlaceholder')"
              class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
              :class="errors.name ? 'border-red-400 focus:ring-red-200' : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'"
            />
            <p v-if="errors.name" class="mt-1.5 text-sm text-red-600">{{ errors.name }}</p>
          </div>

          <!-- Price -->
          <div>
            <label for="svc-price" class="block text-sm font-medium text-slate-700 mb-1.5">
              {{ t('services.price') }}
            </label>
            <div class="relative">
              <input
                id="svc-price"
                v-model.number="form.price"
                type="number"
                min="0"
                step="1000"
                placeholder="50000"
                class="w-full px-3.5 py-2.5 pr-14 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
                :class="errors.price ? 'border-red-400 focus:ring-red-200' : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'"
              />
              <span class="absolute right-3 top-1/2 -translate-y-1/2 text-sm font-medium text-slate-400 pointer-events-none">
                UZS
              </span>
            </div>
            <p v-if="errors.price" class="mt-1.5 text-sm text-red-600">{{ errors.price }}</p>
          </div>

          <!-- Duration -->
          <div>
            <label for="svc-duration" class="block text-sm font-medium text-slate-700 mb-1.5">
              {{ t('services.duration') }}
            </label>
            <select
              id="svc-duration"
              v-model.number="form.duration"
              class="w-full px-3.5 py-2.5 rounded-lg border border-slate-200 text-[15px] text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 transition-colors"
            >
              <option v-for="d in durationOptions" :key="d" :value="d">{{ d }} {{ t('booking.summary.minutes') }}</option>
            </select>
          </div>

          <!-- General error -->
          <div
            v-if="errors.general"
            class="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
          >
            {{ errors.general }}
          </div>

          <!-- Actions -->
          <div class="flex flex-col-reverse sm:flex-row sm:justify-end gap-2 pt-2">
            <button
              type="button"
              class="inline-flex items-center justify-center h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors disabled:opacity-50"
              :disabled="saveMutation.isPending.value"
              @click="closeModal"
            >
              {{ t('common.cancel') }}
            </button>
            <button
              type="submit"
              :disabled="saveMutation.isPending.value"
              class="inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            >
              <svg
                v-if="saveMutation.isPending.value"
                class="h-4 w-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
              </svg>
              {{ saveMutation.isPending.value ? t('settings.saving') : (mode === 'add' ? t('services.addService') : t('services.save')) }}
            </button>
          </div>

          <!-- Delete (edit mode) -->
          <div v-if="mode === 'edit'" class="pt-4 border-t border-slate-100">
            <button
              type="button"
              class="text-sm font-medium text-red-600 hover:text-red-700 transition-colors"
              @click="showConfirmDelete = true"
            >
              {{ t('services.delete') }}
            </button>
          </div>
        </form>

        <!-- Delete confirmation overlay -->
        <Transition name="fade">
          <div
            v-if="showConfirmDelete"
            class="absolute inset-0 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4 rounded-t-2xl md:rounded-2xl"
          >
            <div class="w-full max-w-sm bg-white rounded-xl shadow-xl p-5">
              <h3 class="text-base font-semibold text-slate-900 tracking-tight">
                {{ t('services.deleteConfirm') }}
              </h3>
              <p class="mt-2 text-sm text-slate-600">
                {{ t('services.deleteConfirmDesc') }}
              </p>
              <div class="mt-5 flex flex-col-reverse sm:flex-row sm:justify-end gap-2">
                <button
                  type="button"
                  class="inline-flex items-center justify-center h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors"
                  :disabled="deleteMutation.isPending.value"
                  @click="showConfirmDelete = false"
                >
                  {{ t('services.keep') }}
                </button>
                <button
                  type="button"
                  class="inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-semibold transition-colors disabled:opacity-60"
                  :disabled="deleteMutation.isPending.value"
                  @click="deleteMutation.mutate()"
                >
                  <svg
                    v-if="deleteMutation.isPending.value"
                    class="h-4 w-4 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                    <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                  </svg>
                  {{ t('services.delete') }}
                </button>
              </div>
            </div>
          </div>
        </Transition>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
