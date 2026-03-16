<script setup lang="ts">
import { RouterLink } from 'vue-router'

export interface AppointmentResult {
  id: number
  customer: Record<string, unknown>
  barber: Record<string, unknown>
  date: string
  start_time: string
  end_time: string
  status: string
  payment_method: string
  payment_status: string
  total_price: number
  total_duration: number
  services: { service_id: number | null; service_name: string; service_price: number; service_duration: number }[]
  shop_name?: string
  shop_address?: string
}

const props = defineProps<{
  appointment: AppointmentResult
  barberId: number | string
}>()

function formatPrice(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  return d.toLocaleDateString('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function paymentLabel(method: string, status: string): string {
  if (method === 'ONLINE' && status === 'PAID') return 'Paid online'
  if (method === 'AT_SHOP') return 'Pay at shop'
  return status
}
</script>

<template>
  <div class="flex flex-col items-center text-center px-4 py-10">
    <!-- Checkmark icon -->
    <div class="mb-6">
      <svg
        class="w-20 h-20 text-green-500"
        viewBox="0 0 80 80"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle cx="40" cy="40" r="38" stroke="currentColor" stroke-width="4" />
        <path
          d="M24 40L35 51L56 30"
          stroke="currentColor"
          stroke-width="4"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </div>

    <h1 class="text-2xl font-bold text-ibook-brown-800 mb-2">
      Booking Confirmed!
    </h1>
    <p class="text-ibook-brown-400 mb-8">
      Your appointment has been booked successfully.
    </p>

    <!-- Details card -->
    <div
      class="w-full max-w-md bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-6 text-left space-y-4"
    >
      <!-- Services -->
      <div>
        <div class="text-xs uppercase text-ibook-brown-400 mb-1">Services</div>
        <ul class="space-y-1">
          <li
            v-for="svc in props.appointment.services"
            :key="svc.service_name"
            class="flex justify-between text-sm text-ibook-brown-700"
          >
            <span>{{ svc.service_name }}</span>
            <span class="font-medium">{{ formatPrice(svc.service_price) }}</span>
          </li>
        </ul>
      </div>

      <!-- Date & time -->
      <div>
        <div class="text-xs uppercase text-ibook-brown-400 mb-1">Date & Time</div>
        <div class="text-sm text-ibook-brown-700">
          {{ formatDate(props.appointment.date) }}
        </div>
        <div class="text-sm text-ibook-brown-700">
          {{ props.appointment.start_time }} &ndash; {{ props.appointment.end_time }}
        </div>
      </div>

      <!-- Shop -->
      <div v-if="props.appointment.shop_name">
        <div class="text-xs uppercase text-ibook-brown-400 mb-1">Location</div>
        <div class="text-sm text-ibook-brown-700">
          {{ props.appointment.shop_name }}
        </div>
        <div v-if="props.appointment.shop_address" class="text-xs text-ibook-brown-400">
          {{ props.appointment.shop_address }}
        </div>
      </div>

      <!-- Payment -->
      <div>
        <div class="text-xs uppercase text-ibook-brown-400 mb-1">Payment</div>
        <div class="text-sm text-ibook-brown-700">
          {{
            paymentLabel(
              props.appointment.payment_method,
              props.appointment.payment_status,
            )
          }}
        </div>
      </div>

      <!-- Total -->
      <div class="pt-3 border-t border-ibook-brown-100 flex justify-between">
        <span class="font-medium text-ibook-brown-800">Total</span>
        <span class="font-bold text-ibook-brown-800">
          {{ formatPrice(props.appointment.total_price) }}
        </span>
      </div>
    </div>

    <!-- CTA buttons -->
    <div class="mt-8 w-full max-w-md space-y-3">
      <RouterLink
        to="/customer/appointments"
        class="block w-full py-3 rounded-xl bg-ibook-brown-800 text-white font-semibold text-center hover:bg-ibook-brown-700 transition-colors"
      >
        View My Appointments
      </RouterLink>
      <RouterLink
        :to="`/customer/book/${props.barberId}`"
        class="block w-full py-3 rounded-xl border border-ibook-brown-800 text-ibook-brown-800 font-semibold text-center hover:bg-ibook-brown-50 transition-colors"
      >
        Book Another
      </RouterLink>
    </div>
  </div>
</template>
