<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  totalPrice: number
  paymentMethod: 'ONLINE' | 'AT_SHOP'
  loading?: boolean
}>()

const emit = defineEmits<{
  confirm: [data: { payment_method: 'ONLINE' | 'AT_SHOP' }]
}>()

function formatPrice(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

function onPayOnline() {
  emit('confirm', { payment_method: 'ONLINE' })
}

function onConfirmAtShop() {
  emit('confirm', { payment_method: 'AT_SHOP' })
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex items-baseline justify-between gap-3 px-4 py-3 rounded-lg bg-slate-50 border border-slate-200">
      <span class="text-sm font-medium text-slate-600">{{ t('booking.summary.total') }}</span>
      <span class="text-xl font-bold text-slate-900 tabular-nums">
        {{ formatPrice(props.totalPrice) }}
      </span>
    </div>

    <div v-if="props.paymentMethod === 'AT_SHOP'" class="space-y-4">
      <div class="flex items-start gap-3 p-4 rounded-xl border border-slate-200 bg-white">
        <svg
          class="w-5 h-5 text-slate-500 shrink-0 mt-0.5"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z"
          />
        </svg>
        <i18n-t keypath="booking.payment.atShopInfo" tag="p" class="text-sm text-slate-700">
          <template #price>
            <span class="font-semibold">{{ formatPrice(props.totalPrice) }}</span>
          </template>
        </i18n-t>
      </div>

      <button
        type="button"
        class="w-full h-11 rounded-lg bg-slate-900 text-white font-semibold hover:bg-slate-800 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
        :disabled="props.loading"
        @click="onConfirmAtShop"
      >
        {{ props.loading ? t('booking.payment.booking') : t('booking.payment.confirmBooking') }}
      </button>
    </div>

    <div v-else-if="props.paymentMethod === 'ONLINE'" class="space-y-4">
      <div class="flex items-start gap-3 p-4 rounded-xl border border-slate-200 bg-white">
        <svg
          class="w-5 h-5 text-slate-500 shrink-0 mt-0.5"
          fill="none"
          stroke="currentColor"
          stroke-width="1.7"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"
          />
        </svg>
        <i18n-t keypath="booking.payment.onlineInfo" tag="p" class="text-sm text-slate-700">
          <template #price>
            <span class="font-semibold">{{ formatPrice(props.totalPrice) }}</span>
          </template>
        </i18n-t>
      </div>

      <button
        type="button"
        class="w-full h-11 rounded-lg bg-slate-900 text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        :class="!props.loading ? 'hover:bg-slate-800' : ''"
        :disabled="props.loading"
        @click="onPayOnline"
      >
        <span v-if="props.loading" class="flex items-center justify-center gap-2">
          <svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
          </svg>
          {{ t('booking.payment.preparingCheckout') }}
        </span>
        <span v-else>{{ t('booking.payment.payWithStripe') }}</span>
      </button>
    </div>
  </div>
</template>
