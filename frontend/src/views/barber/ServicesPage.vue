<script setup lang="ts">
import { ref } from 'vue'
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import BarberLayout from '@/layouts/BarberLayout.vue'
import ServiceList from '@/components/services/ServiceList.vue'
import ServiceModal from '@/components/services/ServiceModal.vue'
import type { Service } from '@/components/services/ServiceModal.vue'
import api from '@/lib/axios'

const queryClient = useQueryClient()

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
}

function onModalClose() {
  showModal.value = false
}
</script>

<template>
  <BarberLayout>
    <div class="p-8">
      <!-- Page header -->
      <div class="flex items-center justify-between mb-8">
        <div>
          <h1 class="text-3xl font-bold text-ibook-brown-900">Services</h1>
          <p class="mt-1 text-ibook-brown-500">Manage your service catalog.</p>
        </div>
        <button
          type="button"
          class="px-5 py-2.5 rounded-xl bg-ibook-gold-500 text-white text-sm font-semibold hover:bg-ibook-gold-600 transition-colors shadow-sm cursor-pointer"
          @click="openAddModal"
        >
          + Add Service
        </button>
      </div>

      <!-- Services card -->
      <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-6">
        <div v-if="isLoading" class="py-8 text-center text-ibook-brown-400 text-sm">
          Loading services...
        </div>
        <ServiceList
          v-else
          :services="services ?? []"
          @edit="openEditModal"
        />
      </div>

      <!-- Service modal -->
      <ServiceModal
        v-if="showModal"
        :mode="modalMode"
        :service="selectedService"
        @close="onModalClose"
        @saved="onModalSaved"
      />
    </div>
  </BarberLayout>
</template>
