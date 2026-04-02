<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import AppointmentCard from '@/components/booking/AppointmentCard.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import type { AppointmentData } from '@/components/booking/AppointmentCard.vue'
import api from '@/lib/axios'

const toast = useToast()

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
    toast.success('Appointment cancelled')
  },
  onError: () => {
    toast.error('Failed to cancel appointment. Please try again.')
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
    <div class="max-w-3xl mx-auto px-4 md:px-8 py-6 md:py-10">
      <!-- Page header -->
      <div class="mb-6 md:mb-8">
        <h1 class="text-xl md:text-3xl font-bold text-ibook-brown-900">My Appointments</h1>
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

      <!-- Loading skeleton -->
      <div v-if="isLoading" class="space-y-3">
        <SkeletonBlock v-for="n in 3" :key="n" height="6rem" />
      </div>

      <!-- Empty state -->
      <EmptyState
        v-else-if="!appointments || appointments.length === 0"
        :title="activeTab === 'upcoming' ? 'No upcoming appointments' : 'No past appointments'"
        :description="activeTab === 'upcoming' ? 'Browse barbers and book your first appointment.' : 'Your completed appointments will appear here.'"
        :action-to="activeTab === 'upcoming' ? '/customer/explore' : undefined"
        :action-label="activeTab === 'upcoming' ? 'Find a barber' : undefined"
      />

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
