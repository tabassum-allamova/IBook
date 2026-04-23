<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import BarberLayout from '@/layouts/BarberLayout.vue'
import ServiceList from '@/components/services/ServiceList.vue'
import ServiceModal from '@/components/services/ServiceModal.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import type { Service } from '@/components/services/ServiceModal.vue'
import api from '@/lib/axios'

const toast = useToast()
const queryClient = useQueryClient()
const { t } = useI18n()

const { data: services, isLoading } = useQuery<Service[]>({
  queryKey: ['services'],
  queryFn: async () => {
    const res = await api.get<Service[]>('/api/services/')
    return res.data
  },
})

const showModal = ref(false)
const modalMode = ref<'add' | 'edit'>('add')
const selectedService = ref<Service | undefined>(undefined)

function openAddModal() {
  modalMode.value = 'add'
  selectedService.value = undefined
  showModal.value = true
}

function openEditModal(service: Service) {
  modalMode.value = 'edit'
  selectedService.value = service
  showModal.value = true
}

function onModalSaved() {
  queryClient.invalidateQueries({ queryKey: ['services'] })
  showModal.value = false
  toast.success(t('toasts.saved'))
}

function onModalDeleted() {
  queryClient.invalidateQueries({ queryKey: ['services'] })
  showModal.value = false
  toast.success(t('toasts.deleted'))
}

function onModalClose() {
  showModal.value = false
}
</script>

<template>
  <BarberLayout>
    <section class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
            {{ t('services.title') }}
          </h1>
          <p class="mt-1 text-sm text-slate-600">
            {{ t('services.subtitle') }}
          </p>
        </div>
        <button
          type="button"
          class="inline-flex items-center justify-center gap-1.5 h-10 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 self-start sm:self-auto"
          @click="openAddModal"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m-8-8h16" />
          </svg>
          {{ t('services.addService') }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="space-y-3 max-w-3xl">
        <SkeletonBlock v-for="n in 4" :key="n" height="4rem" />
      </div>

      <!-- Empty -->
      <div
        v-else-if="!services || services.length === 0"
        class="bg-white rounded-xl border border-slate-200 p-12 flex flex-col items-center text-center max-w-3xl"
      >
        <div class="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center mb-4">
          <svg class="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-slate-900 tracking-tight mb-1">{{ t('services.empty') }}</h3>
        <p class="text-sm text-slate-500 max-w-xs leading-relaxed">
          {{ t('services.emptyDesc') }}
        </p>
      </div>

      <!-- Services list -->
      <ServiceList
        v-else
        :services="services"
        @edit="openEditModal"
      />

      <!-- Modal -->
      <ServiceModal
        v-if="showModal"
        :mode="modalMode"
        :service="selectedService"
        @close="onModalClose"
        @saved="onModalSaved"
        @deleted="onModalDeleted"
      />
    </section>
  </BarberLayout>
</template>
