<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import BarberLayout from '@/layouts/BarberLayout.vue'
import BarberDayNav from '@/components/booking/BarberDayNav.vue'
import AppointmentCard from '@/components/booking/AppointmentCard.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import type { AppointmentData } from '@/components/booking/AppointmentCard.vue'
import api from '@/lib/axios'

const toast = useToast()

const queryClient = useQueryClient()

function todayISO(): string {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

const selectedDate = ref(todayISO())

const { data: appointments, isLoading } = useQuery<AppointmentData[]>({
  queryKey: computed(() => ['barber-appointments', selectedDate.value]),
  queryFn: () =>
    api
      .get<AppointmentData[]>('/api/bookings/barber/day/', {
        params: { date: selectedDate.value },
      })
      .then((r) => r.data),
})

// Day summary computations
const appointmentCount = computed(() => appointments.value?.length ?? 0)

const dayRevenue = computed(() => {
  if (!appointments.value) return 0
  return appointments.value
    .filter((a) => a.status === 'CONFIRMED' || a.status === 'COMPLETED')
    .reduce((sum, a) => sum + a.total_price, 0)
})

function formatPrice(price: number): string {
  return price.toLocaleString('en-US') + ' UZS'
}

// Mutations
const actionId = ref<number | null>(null)

const noShowMutation = useMutation({
  mutationFn: (appointmentId: number) =>
    api.post(`/api/bookings/${appointmentId}/no-show/`),
  onMutate: (id) => {
    actionId.value = id
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['barber-appointments'] })
    toast.success('Marked as no-show')
  },
  onError: () => {
    toast.error('Failed to update appointment.')
  },
  onSettled: () => {
    actionId.value = null
  },
})

const cancelMutation = useMutation({
  mutationFn: (appointmentId: number) =>
    api.post(`/api/bookings/${appointmentId}/cancel/`),
  onMutate: (id) => {
    actionId.value = id
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['barber-appointments'] })
    toast.success('Appointment cancelled')
  },
  onError: () => {
    toast.error('Failed to cancel appointment.')
  },
  onSettled: () => {
    actionId.value = null
  },
})

function handleNoShow(id: number) {
  noShowMutation.mutate(id)
}

function handleCancel(id: number) {
  cancelMutation.mutate(id)
}
</script>

<template>
  <BarberLayout>
    <div class="p-4 md:p-8">
      <!-- Page header -->
      <div class="mb-6">
        <h1 class="text-xl md:text-3xl font-bold text-ibook-brown-900">My Appointments</h1>
      </div>

      <!-- Date navigation -->
      <div class="mb-6">
        <BarberDayNav v-model="selectedDate" />
      </div>

      <!-- Day summary -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">Appointments</p>
          <p class="text-3xl font-bold text-ibook-brown-900">{{ appointmentCount }}</p>
          <p class="text-xs text-ibook-brown-400 mt-1">for this day</p>
        </div>
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">Revenue</p>
          <p class="text-3xl font-bold text-ibook-gold-500">{{ formatPrice(dayRevenue) }}</p>
          <p class="text-xs text-ibook-brown-400 mt-1">confirmed + completed</p>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="isLoading" class="space-y-3">
        <SkeletonBlock v-for="n in 3" :key="n" height="5rem" />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!appointments || appointments.length === 0"
        class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-12 flex flex-col items-center text-center"
      >
        <div
          class="w-16 h-16 rounded-full bg-ibook-brown-100 flex items-center justify-center mb-4"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-8 w-8 text-ibook-brown-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="1.5"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-ibook-brown-800 mb-2">
          No appointments for this date
        </h3>
        <p class="text-ibook-brown-500 text-sm max-w-xs">
          When customers book with you for this day, their appointments will appear here.
        </p>
      </div>

      <!-- Appointment list -->
      <div v-else class="space-y-4">
        <AppointmentCard
          v-for="appt in appointments"
          :key="appt.id"
          :appointment="appt"
          variant="barber"
          :loading="actionId === appt.id"
          @noshow="handleNoShow"
          @cancel="handleCancel"
        />
      </div>
    </div>
  </BarberLayout>
</template>
