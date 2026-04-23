<script setup lang="ts">
import { RouterLink } from 'vue-router'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

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

const BROWSER_LOCALES: Record<string, string> = {
  en: 'en-US',
  ru: 'ru-RU',
  uz: 'uz-UZ',
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + 'T00:00:00')
  const tag = BROWSER_LOCALES[locale.value] ?? 'en-US'
  return d.toLocaleDateString(tag, {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

function paymentLabel(method: string, status: string): string {
  if (method === 'ONLINE' && status === 'PAID') return t('booking.confirmation.paymentStatus.paidOnline')
  if (method === 'ONLINE' && status === 'PENDING') return t('booking.confirmation.paymentStatus.pending')
  if (method === 'ONLINE' && status === 'DECLINED') return t('booking.confirmation.paymentStatus.declined')
  if (method === 'AT_SHOP') return t('booking.confirmation.paymentStatus.atShop')
  return t('booking.confirmation.paymentStatus.unavailable')
}
</script>

<template>
  <div class="flex flex-col items-center text-center px-4 py-8">
    <!-- Checkmark icon -->
    <div class="mb-5 inline-flex items-center justify-center h-16 w-16 rounded-full bg-emerald-50 border border-emerald-200">
      <svg
        class="w-9 h-9 text-emerald-600"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2.4"
      >
        <path d="M5 13l4 4L19 7" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </div>

    <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight mb-2">
      {{ t('booking.confirmation.title') }}
    </h1>
    <p class="text-slate-500 mb-8">
      {{ t('booking.confirmation.subtitle') }}
    </p>

    <!-- Details card -->
    <div
      class="w-full max-w-md bg-white rounded-xl border border-slate-200 p-5 md:p-6 text-left space-y-5"
    >
      <!-- Services -->
      <div>
        <div class="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-2">{{ t('booking.confirmation.sections.services') }}</div>
        <ul class="space-y-1.5">
          <li
            v-for="svc in props.appointment.services"
            :key="svc.service_name"
            class="flex justify-between gap-3 text-sm text-slate-700"
          >
            <span class="truncate">{{ svc.service_name }}</span>
            <span class="font-medium text-slate-900 tabular-nums">{{ formatPrice(svc.service_price) }}</span>
          </li>
        </ul>
      </div>

      <!-- Date & time -->
      <div>
        <div class="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-2">{{ t('booking.confirmation.sections.dateTime') }}</div>
        <div class="text-sm text-slate-900 font-medium">
          {{ formatDate(props.appointment.date) }}
        </div>
        <div class="text-sm text-slate-600 mt-0.5 tabular-nums">
          {{ props.appointment.start_time }} &ndash; {{ props.appointment.end_time }}
        </div>
      </div>

      <!-- Shop -->
      <div v-if="props.appointment.shop_name">
        <div class="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-2">{{ t('booking.confirmation.sections.location') }}</div>
        <div class="text-sm text-slate-900 font-medium">
          {{ props.appointment.shop_name }}
        </div>
        <div v-if="props.appointment.shop_address" class="text-sm text-slate-500 mt-0.5">
          {{ props.appointment.shop_address }}
        </div>
      </div>

      <!-- Payment -->
      <div>
        <div class="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-2">{{ t('booking.confirmation.sections.payment') }}</div>
        <div class="text-sm text-slate-700">
          {{
            paymentLabel(
              props.appointment.payment_method,
              props.appointment.payment_status,
            )
          }}
        </div>
      </div>

      <!-- Total -->
      <div class="pt-4 border-t border-slate-100 flex items-baseline justify-between">
        <span class="text-sm font-medium text-slate-500">{{ t('booking.confirmation.sections.total') }}</span>
        <span class="text-lg font-bold text-slate-900 tabular-nums">
          {{ formatPrice(props.appointment.total_price) }}
        </span>
      </div>
    </div>

    <!-- CTA buttons -->
    <div class="mt-6 w-full max-w-md space-y-3">
      <RouterLink
        to="/customer/appointments"
        class="block w-full h-11 inline-flex items-center justify-center rounded-lg bg-slate-900 text-white font-semibold hover:bg-slate-800 transition-colors"
      >
        {{ t('booking.confirmation.viewAppointments') }}
      </RouterLink>
      <RouterLink
        :to="`/customer/book/${props.barberId}`"
        class="block w-full h-11 inline-flex items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-700 font-semibold hover:border-slate-400 hover:text-slate-900 transition-colors"
      >
        {{ t('booking.confirmation.bookAnother') }}
      </RouterLink>
    </div>
  </div>
</template>
