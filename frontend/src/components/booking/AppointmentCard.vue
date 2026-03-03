<script setup lang="ts">
export interface AppointmentServiceItem {
  service_name: string
  service_price: number
  service_duration: number
}

export interface AppointmentData {
  id: number
  customer: number
  barber: number
  customer_name?: string
  barber_name?: string
  date: string
  start_time: string
  end_time: string
  status: 'CONFIRMED' | 'COMPLETED' | 'CANCELLED' | 'NO_SHOW'
  payment_method: string
  payment_status: string
  total_price: number
  total_duration: number
  services: AppointmentServiceItem[]
  shop_name?: string | null
  shop_address?: string | null
}

const props = defineProps<{
  appointment: AppointmentData
  variant: 'customer' | 'barber'
  loading?: boolean
}>()

const emit = defineEmits<{
  cancel: [id: number]
  reschedule: [appointment: AppointmentData]
  noshow: [id: number]
}>()

const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
  CONFIRMED: { bg: 'bg-green-100', text: 'text-green-800', label: 'Confirmed' },
  COMPLETED: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'Completed' },
  CANCELLED: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Cancelled' },
  NO_SHOW: { bg: 'bg-red-100', text: 'text-red-800', label: 'No-show' },
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

function formatPrice(price: number): string {
  return price.toLocaleString('en-US') + ' UZS'
}

function servicesSummary(services: AppointmentServiceItem[]): string {
  return services.map((s) => `${s.service_name} (${s.service_duration}min)`).join(', ')
}
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-ibook-brown-100 p-4">
    <!-- Top row: date + time, status badge -->
    <div class="flex items-center justify-between mb-3">
      <div class="text-sm font-semibold text-ibook-brown-800">
        {{ formatDate(props.appointment.date) }} at {{ props.appointment.start_time }}
        <span class="text-ibook-brown-400 font-normal">
          - {{ props.appointment.end_time }}
        </span>
      </div>
      <span
        class="text-xs font-medium px-2.5 py-0.5 rounded-full"
        :class="[
          statusConfig[props.appointment.status]?.bg ?? 'bg-gray-100',
          statusConfig[props.appointment.status]?.text ?? 'text-gray-600',
        ]"
      >
        {{ statusConfig[props.appointment.status]?.label ?? props.appointment.status }}
      </span>
    </div>

    <!-- Middle: names -->
    <div class="mb-2">
      <p v-if="props.variant === 'customer'" class="text-sm text-ibook-brown-700">
        <span class="font-medium">{{ props.appointment.barber_name }}</span>
        <span v-if="props.appointment.shop_name" class="text-ibook-brown-400">
          &middot; {{ props.appointment.shop_name }}
        </span>
      </p>
      <p v-else class="text-sm text-ibook-brown-700">
        <span class="font-medium">{{ props.appointment.customer_name }}</span>
      </p>
    </div>

    <!-- Services list -->
    <p class="text-xs text-ibook-brown-500 mb-3">
      {{ servicesSummary(props.appointment.services) }}
    </p>

    <!-- Bottom row: price + actions -->
    <div class="flex items-center justify-between">
      <span class="text-sm font-bold text-ibook-brown-900">
        {{ formatPrice(props.appointment.total_price) }}
      </span>

      <!-- Action buttons (only for CONFIRMED) -->
      <div v-if="props.appointment.status === 'CONFIRMED'" class="flex items-center gap-2">
        <template v-if="props.variant === 'customer'">
          <button
            type="button"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border border-red-300 text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            :disabled="props.loading"
            @click="emit('cancel', props.appointment.id)"
          >
            <span v-if="props.loading" class="inline-block w-3 h-3 border-2 border-red-300 border-t-transparent rounded-full animate-spin mr-1 align-middle" />
            Cancel
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border border-ibook-brown-300 text-ibook-brown-700 hover:bg-ibook-brown-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            :disabled="props.loading"
            @click="emit('reschedule', props.appointment)"
          >
            Reschedule
          </button>
        </template>
        <template v-else>
          <button
            type="button"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border border-red-300 text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            :disabled="props.loading"
            @click="emit('noshow', props.appointment.id)"
          >
            <span v-if="props.loading" class="inline-block w-3 h-3 border-2 border-red-300 border-t-transparent rounded-full animate-spin mr-1 align-middle" />
            No-show
          </button>
          <button
            type="button"
            class="px-3 py-1.5 text-xs font-medium rounded-lg border border-gray-300 text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
            :disabled="props.loading"
            @click="emit('cancel', props.appointment.id)"
          >
            Cancel
          </button>
        </template>
      </div>
    </div>
  </div>
</template>
