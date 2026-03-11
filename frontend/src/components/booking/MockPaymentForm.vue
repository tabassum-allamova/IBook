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
const cardError = ref('')
const expiryError = ref('')
const cvvError = ref('')

const buttonLabel = computed(() =>
  paymentMethod.value === 'ONLINE' ? 'Confirm & Pay' : 'Confirm Booking',
)

const rawCard = computed(() => cardNumber.value.replace(/\s/g, ''))

const isOnlineValid = computed(() => {
  if (paymentMethod.value !== 'ONLINE') return true
  return rawCard.value.length >= 13 && rawCard.value.length <= 19
    && expiry.value.length === 5
    && cvv.value.length >= 3
})

function formatCardInput(e: Event) {
  const input = e.target as HTMLInputElement
  const digits = input.value.replace(/\D/g, '').slice(0, 16)
  cardNumber.value = digits.replace(/(.{4})/g, '$1 ').trim()
  cardError.value = ''
}

function formatExpiryInput(e: Event) {
  const input = e.target as HTMLInputElement
  let digits = input.value.replace(/\D/g, '').slice(0, 4)
  if (digits.length >= 3) {
    digits = digits.slice(0, 2) + '/' + digits.slice(2)
  }
  expiry.value = digits
  expiryError.value = ''
}

function formatCvvInput(e: Event) {
  const input = e.target as HTMLInputElement
  cvv.value = input.value.replace(/\D/g, '').slice(0, 3)
  cvvError.value = ''
}

function formatPrice(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

function validate(): boolean {
  let valid = true
  if (paymentMethod.value !== 'ONLINE') return true

  if (rawCard.value.length < 13) {
    cardError.value = 'Enter a valid card number'
    valid = false
  }
  if (!/^\d{2}\/\d{2}$/.test(expiry.value)) {
    expiryError.value = 'Use MM/YY format'
    valid = false
  }
  if (cvv.value.length < 3) {
    cvvError.value = 'Enter 3 or 4 digit CVV'
    valid = false
  }
  return valid
}

function onSubmit() {
  if (!validate()) return
  const data: { payment_method: 'ONLINE' | 'AT_SHOP'; card_number?: string } = {
    payment_method: paymentMethod.value,
  }
  if (paymentMethod.value === 'ONLINE') {
    data.card_number = rawCard.value
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
          :value="cardNumber"
          type="text"
          inputmode="numeric"
          placeholder="4111 1111 1111 1111"
          maxlength="19"
          class="w-full px-3 py-2 rounded-lg border text-ibook-brown-800 placeholder:text-ibook-brown-300 focus:outline-none tracking-wider"
          :class="cardError ? 'border-red-400 focus:border-red-400' : 'border-ibook-brown-200 focus:border-ibook-gold-400'"
          @input="formatCardInput"
        />
        <p v-if="cardError" class="mt-1 text-xs text-red-500">{{ cardError }}</p>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="block text-sm font-medium text-ibook-brown-700 mb-1">
            Expiry
          </label>
          <input
            :value="expiry"
            type="text"
            inputmode="numeric"
            placeholder="MM/YY"
            maxlength="5"
            class="w-full px-3 py-2 rounded-lg border text-ibook-brown-800 placeholder:text-ibook-brown-300 focus:outline-none"
            :class="expiryError ? 'border-red-400 focus:border-red-400' : 'border-ibook-brown-200 focus:border-ibook-gold-400'"
            @input="formatExpiryInput"
          />
          <p v-if="expiryError" class="mt-1 text-xs text-red-500">{{ expiryError }}</p>
        </div>
        <div>
          <label class="block text-sm font-medium text-ibook-brown-700 mb-1">
            CVV
          </label>
          <input
            :value="cvv"
            type="text"
            inputmode="numeric"
            placeholder="123"
            maxlength="3"
            class="w-full px-3 py-2 rounded-lg border text-ibook-brown-800 placeholder:text-ibook-brown-300 focus:outline-none"
            :class="cvvError ? 'border-red-400 focus:border-red-400' : 'border-ibook-brown-200 focus:border-ibook-gold-400'"
            @input="formatCvvInput"
          />
          <p v-if="cvvError" class="mt-1 text-xs text-red-500">{{ cvvError }}</p>
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
      :disabled="props.loading || !isOnlineValid"
      @click="onSubmit"
    >
      <span v-if="props.loading">Processing...</span>
      <span v-else>{{ buttonLabel }}</span>
    </button>
  </div>
</template>
