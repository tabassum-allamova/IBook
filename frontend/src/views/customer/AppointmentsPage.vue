<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import AppointmentCard from '@/components/booking/AppointmentCard.vue'
import type { AppointmentData } from '@/components/booking/AppointmentCard.vue'
import api from '@/lib/axios'

const router = useRouter()
const queryClient = useQueryClient()

const activeTab = ref<'upcoming' | 'past'>('upcoming')

// Map tab to backend URL path
const tabEndpoints: Record<'upcoming' | 'past', string> = {
  upcoming: '/api/bookings/my/upcoming/',
  past: '/api/bookings/my/past/',
}

const { data: appointments, isLoading } = useQuery<AppointmentData[]>({
  queryKey: computed(() => ['appointments', activeTab.value]),
  queryFn: () =>
    api.get<AppointmentData[]>(tabEndpoints[activeTab.value]).then((r) => r.data),
})

const cancellingId = ref<number | null>(null)

const cancelMutation = useMutation({
  mutationFn: (appointmentId: number) =>
    api.post(`/api/bookings/${appointmentId}/cancel/`),
  onMutate: (id) => {
    cancellingId.value = id
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['appointments'] })
  },
  onSettled: () => {
    cancellingId.value = null
  },
})

function handleCancel(id: number) {
  cancelMutation.mutate(id)
}

async function handleReschedule(appointment: AppointmentData) {
  // Reschedule = cancel existing + navigate to booking page with same barber/services
  cancellingId.value = appointment.id
  try {
    await api.post(`/api/bookings/${appointment.id}/cancel/`)
    queryClient.invalidateQueries({ queryKey: ['appointments'] })

    const serviceIds = appointment.services
      .map((s) => s.service_id)
      .filter((id): id is number => id !== null)
      .join(',')

    // Navigate to booking page with barber pre-selected and services for pre-selection
    router.push({
      path: `/customer/book/${appointment.barber}`,
      query: {
        reschedule: 'true',
        ...(serviceIds ? { services: serviceIds } : {}),
      },
    })
  } catch {
    // Cancel failed -- stay on page
  } finally {
    cancellingId.value = null
  }
}
</script>

<template>
  <CustomerLayout>
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <!-- Page header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-ibook-brown-900">My Appointments</h1>
        <p class="mt-1 text-ibook-brown-500">View and manage your bookings.</p>
      </div>

      <!-- Tab buttons -->
      <div class="flex border-b border-ibook-brown-200 mb-6">
        <button
          type="button"
          class="px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer -mb-px"
          :class="
            activeTab === 'upcoming'
              ? 'text-ibook-brown-900 border-b-2 border-ibook-brown-800'
              : 'text-ibook-brown-400 hover:text-ibook-brown-600'
          "
          @click="activeTab = 'upcoming'"
        >
          Upcoming
        </button>
        <button
          type="button"
          class="px-4 py-2.5 text-sm font-medium transition-colors cursor-pointer -mb-px"
          :class="
            activeTab === 'past'
              ? 'text-ibook-brown-900 border-b-2 border-ibook-brown-800'
              : 'text-ibook-brown-400 hover:text-ibook-brown-600'
          "
          @click="activeTab = 'past'"
        >
          Past
        </button>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="py-12 text-center text-ibook-brown-400 text-sm">
        Loading appointments...
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
          {{ activeTab === 'upcoming' ? 'No upcoming appointments' : 'No past appointments' }}
        </h3>
        <p class="text-ibook-brown-500 text-sm max-w-xs">
          {{
            activeTab === 'upcoming'
              ? 'Book an appointment with a barber to get started.'
              : 'Your completed, cancelled, or missed appointments will appear here.'
          }}
        </p>
      </div>

      <!-- Appointment list -->
      <div v-else class="space-y-4">
        <AppointmentCard
          v-for="appt in appointments"
          :key="appt.id"
          :appointment="appt"
          variant="customer"
          :loading="cancellingId === appt.id"
          @cancel="handleCancel"
          @reschedule="handleReschedule"
        />
      </div>
    </div>
  </CustomerLayout>
</template>
