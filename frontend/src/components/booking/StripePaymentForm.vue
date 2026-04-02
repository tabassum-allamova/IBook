<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { loadStripe } from '@stripe/stripe-js'
import type { Stripe, StripeElements } from '@stripe/stripe-js'
import api from '@/lib/axios'

const props = defineProps<{
  totalPrice: number
  paymentMethod: 'ONLINE' | 'AT_SHOP'
}>()

const emit = defineEmits<{
  confirm: [data: { payment_method: 'ONLINE' | 'AT_SHOP' }]
  error: [message: string]
}>()

// Template refs
const cardRef = ref<HTMLDivElement | null>(null)

// Component state
const loading = ref(false)
const submitting = ref(false)
const stripeConfigured = ref(true)
const errorMessage = ref('')

// Stripe instances (not reactive — avoid Proxy wrapping)
let stripeInstance: Stripe | null = null
let elementsInstance: StripeElements | null = null

function formatPrice(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

async function initStripe() {
  const publishableKey = import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY as string
  if (!publishableKey) {
    stripeConfigured.value = false
    return
  }

  loading.value = true
  errorMessage.value = ''

  try {
    // Get client_secret from backend
    const response = await api.post('/api/bookings/create-payment-intent/', {
      amount: props.totalPrice,
    })
    const clientSecret: string = response.data.client_secret

    // Load Stripe
    stripeInstance = await loadStripe(publishableKey)
    if (!stripeInstance) {
      errorMessage.value = 'Failed to load Stripe. Please refresh and try again.'
      loading.value = false
      return
    }

    // Create elements
    elementsInstance = stripeInstance.elements({
      clientSecret,
      appearance: {
        theme: 'flat',
        variables: {
          colorPrimary: '#542f12',
          colorBackground: '#ffffff',
          colorText: '#3d1f08',
          colorDanger: '#ef4444',
          fontFamily: 'system-ui, sans-serif',
          borderRadius: '8px',
        },
      },
    })

    // Mount payment element after DOM is ready
    const paymentElement = elementsInstance.create('payment')
    if (cardRef.value) {
      paymentElement.mount(cardRef.value)
    }
  } catch (err: unknown) {
    const e = err as { response?: { data?: { detail?: string } }; message?: string }
    errorMessage.value =
      e.response?.data?.detail ?? e.message ?? 'Failed to initialize payment. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (props.paymentMethod === 'ONLINE') {
    initStripe()
  }
})

// Re-init when switching to ONLINE
watch(
  () => props.paymentMethod,
  (method) => {
    if (method === 'ONLINE' && !elementsInstance) {
      initStripe()
    }
  },
)

async function onConfirmOnline() {
  if (!stripeInstance || !elementsInstance) {
    emit('error', 'Payment form not ready. Please wait and try again.')
    return
  }

  submitting.value = true
  errorMessage.value = ''

  try {
    const result = await stripeInstance.confirmPayment({
      elements: elementsInstance,
      confirmParams: {
        return_url: window.location.origin + '/customer/appointments',
      },
      redirect: 'if_required',
    })

    if (result.error) {
      errorMessage.value = result.error.message ?? 'Payment failed. Please try again.'
      emit('error', errorMessage.value)
    } else {
      emit('confirm', { payment_method: 'ONLINE' })
    }
  } catch (err: unknown) {
    const e = err as { message?: string }
    errorMessage.value = e.message ?? 'Unexpected error during payment.'
    emit('error', errorMessage.value)
  } finally {
    submitting.value = false
  }
}

function onConfirmAtShop() {
  emit('confirm', { payment_method: 'AT_SHOP' })
}
</script>

<template>
  <div class="space-y-6">
    <!-- Total price display -->
    <div class="text-center">
      <div class="text-sm text-ibook-brown-400">Total</div>
      <div class="text-2xl font-bold text-ibook-brown-800">
        {{ formatPrice(props.totalPrice) }}
      </div>
    </div>

    <!-- AT_SHOP payment -->
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

    <!-- ONLINE payment -->
    <div v-else-if="props.paymentMethod === 'ONLINE'" class="space-y-4">
      <!-- Stripe not configured fallback -->
      <div
        v-if="!stripeConfigured"
        class="p-4 rounded-xl border border-amber-200 bg-amber-50 text-amber-800 text-sm"
      >
        Online payments are not configured. Please select "Pay at Shop" to continue.
      </div>

      <!-- Loading state -->
      <div
        v-else-if="loading"
        class="py-8 flex flex-col items-center gap-3 text-ibook-brown-400"
      >
        <svg
          class="w-8 h-8 animate-spin"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          />
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
          />
        </svg>
        <span class="text-sm">Preparing secure payment form...</span>
      </div>

      <!-- Stripe Elements mount target -->
      <div v-else-if="!errorMessage">
        <div ref="cardRef" class="min-h-[120px]" />
      </div>

      <!-- Init error -->
      <div
        v-if="errorMessage && !loading"
        class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm"
      >
        {{ errorMessage }}
      </div>

      <!-- Pay button (only shown when Stripe is ready) -->
      <button
        v-if="stripeConfigured && !loading"
        type="button"
        class="w-full py-3 rounded-xl bg-ibook-brown-800 text-white font-semibold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        :class="!submitting ? 'hover:bg-ibook-brown-700' : ''"
        :disabled="submitting || !!errorMessage"
        @click="onConfirmOnline"
      >
        <span v-if="submitting">Processing...</span>
        <span v-else>Confirm & Pay</span>
      </button>
    </div>
  </div>
</template>
