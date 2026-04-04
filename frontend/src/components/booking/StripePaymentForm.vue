<script setup lang="ts">
import { ref } from 'vue'
import api from '@/lib/axios'

const props = defineProps<{
  totalPrice: number
  paymentMethod: 'ONLINE' | 'AT_SHOP'
}>()

const emit = defineEmits<{
  confirm: [data: { payment_method: 'ONLINE' | 'AT_SHOP'; checkoutUrl?: string }]
  error: [message: string]
}>()

const loading = ref(false)
const errorMessage = ref('')

function formatPrice(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

async function onPayOnline() {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await api.post('/api/bookings/create-checkout-session/', {
      amount: props.totalPrice,
      description: 'IBook barbershop appointment',
    })

    if (response.data.url) {
      emit('confirm', { payment_method: 'ONLINE', checkoutUrl: response.data.url })
    }
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    errorMessage.value =
      e.response?.data?.detail ?? e.message ?? 'Failed to start payment. Please try again.'
    emit('error', errorMessage.value)
    loading.value = false
  }
}

function onConfirmAtShop() {
  emit('confirm', { payment_method: 'AT_SHOP' })
}
</script>

<template>
  <div class="space-y-6">
    <div class="text-center">
      <div class="text-sm text-ibook-brown-400">Total</div>
      <div class="text-2xl font-bold text-ibook-brown-800">
        {{ formatPrice(props.totalPrice) }}
      </div>
    </div>

    <div v-if="props.paymentMethod === 'AT_SHOP'" class="space-y-4">
      <div
        class="flex items-center gap-3 p-4 rounded-xl border border-ibook-gold-400 bg-ibook-brown-50"
      >
        <svg
          class="w-5 h-5 text-ibook-brown-600 shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
        <p class="text-sm text-ibook-brown-700">
          You will pay <span class="font-semibold">{{ formatPrice(props.totalPrice) }}</span>
          at the shop on the day of your appointment.
        </p>
      </div>

      <button
        type="button"
        class="w-full py-3 rounded-xl bg-ibook-brown-800 text-white font-semibold hover:bg-ibook-brown-700 transition-colors cursor-pointer"
        @click="onConfirmAtShop"
      >
        Confirm Booking
      </button>
    </div>

    <div v-else-if="props.paymentMethod === 'ONLINE'" class="space-y-4">
      <div
        class="flex items-center gap-3 p-4 rounded-xl border border-ibook-brown-200 bg-ibook-brown-50"
      >
        <svg
          class="w-5 h-5 text-ibook-brown-600 shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
          />
        </svg>
        <p class="text-sm text-ibook-brown-700">
          You will be redirected to Stripe's secure payment page to complete your
          <span class="font-semibold">{{ formatPrice(props.totalPrice) }}</span> payment.
        </p>
      </div>

      <div
        v-if="errorMessage"
        class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm"
      >
        {{ errorMessage }}
      </div>

      <button
        type="button"
        class="w-full py-3 rounded-xl bg-ibook-brown-800 text-white font-semibold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        :class="!loading ? 'hover:bg-ibook-brown-700' : ''"
        :disabled="loading"
        @click="onPayOnline"
      >
        <span v-if="loading" class="flex items-center justify-center gap-2">
          <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          Redirecting to Stripe...
        </span>
        <span v-else>Pay with Stripe</span>
      </button>
    </div>
  </div>
</template>
