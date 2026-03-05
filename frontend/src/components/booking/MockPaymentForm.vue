<script setup lang="ts">
import { ref, computed } from 'vue'

const props = defineProps<{
  totalPrice: number
  loading?: boolean
  error?: string
}>()

const emit = defineEmits<{
  confirm: [data: { payment_method: 'ONLINE' | 'AT_SHOP'; card_number?: string }]
}>()

const paymentMethod = ref<'ONLINE' | 'AT_SHOP'>('ONLINE')
const cardNumber = ref('')
const expiry = ref('')
const cvv = ref('')

const buttonLabel = computed(() =>
  paymentMethod.value === 'ONLINE' ? 'Confirm & Pay' : 'Confirm Booking',
)

function formatPrice(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

function onSubmit() {
  const data: { payment_method: 'ONLINE' | 'AT_SHOP'; card_number?: string } = {
    payment_method: paymentMethod.value,
  }
  if (paymentMethod.value === 'ONLINE') {
    data.card_number = cardNumber.value.replace(/\s/g, '')
  }
  emit('confirm', data)
}
</script>

<template>
  <div class="space-y-6">
    <!-- Total price -->
    <div class="text-center">
      <div class="text-sm text-ibook-brown-400">Total</div>
      <div class="text-2xl font-bold text-ibook-brown-800">
        {{ formatPrice(props.totalPrice) }}
      </div>
    </div>

    <!-- Payment method radio -->
    <div class="space-y-3">
      <label
        class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors"
        :class="
          paymentMethod === 'ONLINE'
            ? 'border-ibook-gold-400 bg-ibook-brown-50'
            : 'border-ibook-brown-200 bg-white'
        "
      >
        <input
          v-model="paymentMethod"
          type="radio"
          value="ONLINE"
          class="w-4 h-4 accent-ibook-gold-500"
        />
        <span class="font-medium text-ibook-brown-800">Pay Online</span>
      </label>

      <label
        class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors"
        :class="
          paymentMethod === 'AT_SHOP'
            ? 'border-ibook-gold-400 bg-ibook-brown-50'
            : 'border-ibook-brown-200 bg-white'
        "
      >
        <input
          v-model="paymentMethod"
          type="radio"
          value="AT_SHOP"
          class="w-4 h-4 accent-ibook-gold-500"
        />
        <span class="font-medium text-ibook-brown-800">Pay at Shop</span>
      </label>
    </div>

    <!-- Card form (online only) -->
    <div v-if="paymentMethod === 'ONLINE'" class="space-y-3">
      <div>
        <label class="block text-sm font-medium text-ibook-brown-700 mb-1">
          Card Number
        </label>
        <input
          v-model="cardNumber"
          type="text"
          placeholder="4111 1111 1111 1111"
          class="w-full px-3 py-2 rounded-lg border border-ibook-brown-200 text-ibook-brown-800 placeholder:text-ibook-brown-300 focus:outline-none focus:border-ibook-gold-400"
        />
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm font-medium text-ibook-brown-700 mb-1">
            Expiry
          </label>
          <input
            v-model="expiry"
            type="text"
            placeholder="MM/YY"
            class="w-full px-3 py-2 rounded-lg border border-ibook-brown-200 text-ibook-brown-800 placeholder:text-ibook-brown-300 focus:outline-none focus:border-ibook-gold-400"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-ibook-brown-700 mb-1">
            CVV
          </label>
          <input
            v-model="cvv"
            type="text"
            placeholder="123"
            class="w-full px-3 py-2 rounded-lg border border-ibook-brown-200 text-ibook-brown-800 placeholder:text-ibook-brown-300 focus:outline-none focus:border-ibook-gold-400"
          />
        </div>
      </div>
    </div>

    <!-- Error message -->
    <div
      v-if="props.error"
      class="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm"
    >
      {{ props.error }}
    </div>

    <!-- Submit button -->
    <button
      type="button"
      class="w-full py-3 rounded-xl bg-ibook-brown-800 text-white font-semibold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
      :class="!props.loading ? 'hover:bg-ibook-brown-700' : ''"
      :disabled="props.loading"
      @click="onSubmit"
    >
      <span v-if="props.loading">Processing...</span>
      <span v-else>{{ buttonLabel }}</span>
    </button>
  </div>
</template>
