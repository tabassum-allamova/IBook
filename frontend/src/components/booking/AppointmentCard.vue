<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { computed } from 'vue'

const { t } = useI18n()

export interface AppointmentServiceItem {
  service_id: number | null
  service_name: string
  service_price: number
  service_duration: number
}

export interface RiskPayload {
  score: number
  band: 'low' | 'medium' | 'high'
  factors: string[]
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
  has_review?: boolean
  risk?: RiskPayload | null
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

const statusConfig = computed<Record<string, { dot: string; text: string; label: string }>>(() => ({
  CONFIRMED: { dot: 'bg-emerald-500', text: 'text-emerald-700', label: t('appointments.status.confirmed') },
  COMPLETED: { dot: 'bg-slate-400', text: 'text-slate-600', label: t('appointments.status.completed') },
  CANCELLED: { dot: 'bg-slate-300', text: 'text-slate-500', label: t('appointments.status.cancelled') },
  NO_SHOW: { dot: 'bg-red-500', text: 'text-red-700', label: t('appointments.status.noShow') },
}))

const riskConfig: Record<'low' | 'medium' | 'high', { pill: string; dot: string; label: string }> = {
  low: {
    pill: 'bg-emerald-50 text-emerald-800 border border-emerald-200',
    dot: 'bg-emerald-500',
    label: 'Low no-show risk',
  },
  medium: {
    pill: 'bg-amber-50 text-amber-900 border border-amber-200',
    dot: 'bg-amber-500',
    label: 'Medium no-show risk',
  },
  high: {
    pill: 'bg-red-50 text-red-800 border border-red-200',
    dot: 'bg-red-500',
    label: 'High no-show risk',
  },
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}

function formatTime(t: string): string {
  return t.slice(0, 5)
}

function formatPrice(price: number): string {
  return price.toLocaleString('en-US') + ' UZS'
}
</script>

<template>
  <article class="bg-white rounded-xl border border-slate-200 p-5 md:p-6">
    <!-- Top row: date/time + status -->
    <div class="flex items-start justify-between gap-3 mb-3">
      <div class="min-w-0">
        <p class="text-base font-semibold text-slate-900 tracking-tight">
          {{ formatDate(props.appointment.date) }}
          <span class="text-slate-400 font-normal mx-1">·</span>
          <span class="tabular-nums">
            {{ formatTime(props.appointment.start_time) }} – {{ formatTime(props.appointment.end_time) }}
          </span>
        </p>
        <p class="mt-1 text-sm text-slate-600">
          <template v-if="props.variant === 'customer'">
            <span class="font-medium text-slate-900">{{ props.appointment.barber_name }}</span>
            <span v-if="props.appointment.shop_name" class="text-slate-400"> · {{ props.appointment.shop_name }}</span>
          </template>
          <template v-else>
            <span class="font-medium text-slate-900">{{ props.appointment.customer_name }}</span>
          </template>
        </p>
      </div>

      <span
        class="inline-flex items-center gap-1.5 flex-shrink-0 text-sm font-medium"
        :class="statusConfig[props.appointment.status]?.text ?? 'text-slate-500'"
      >
        <span
          class="h-1.5 w-1.5 rounded-full"
          :class="statusConfig[props.appointment.status]?.dot ?? 'bg-slate-400'"
        ></span>
        {{ statusConfig[props.appointment.status]?.label ?? props.appointment.status }}
      </span>
    </div>

    <!-- Services -->
    <ul class="flex flex-wrap gap-1.5 mb-4">
      <li
        v-for="s in props.appointment.services"
        :key="`${s.service_id ?? s.service_name}`"
        class="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-slate-50 border border-slate-100 text-sm text-slate-700"
      >
        <span>{{ s.service_name }}</span>
        <span class="text-slate-400">{{ s.service_duration }}m</span>
      </li>
    </ul>

    <!-- No-show risk (barber view only, upcoming confirmed bookings) -->
    <div
      v-if="props.variant === 'barber' && props.appointment.risk"
      class="flex flex-wrap items-center gap-1.5 mb-4"
    >
      <span
        :class="[
          'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-medium',
          riskConfig[props.appointment.risk.band].pill,
        ]"
        :title="`No-show probability: ${(props.appointment.risk.score * 100).toFixed(0)}%`"
      >
        <span
          class="h-1.5 w-1.5 rounded-full"
          :class="riskConfig[props.appointment.risk.band].dot"
        ></span>
        {{ riskConfig[props.appointment.risk.band].label }}
      </span>
      <span
        v-for="factor in props.appointment.risk.factors"
        :key="factor"
        class="inline-flex items-center px-2 py-1 rounded-md bg-slate-50 border border-slate-100 text-sm text-slate-600"
      >
        {{ factor }}
      </span>
    </div>

    <!-- Bottom row: total + actions -->
    <div class="flex items-center justify-between gap-3 pt-4 border-t border-slate-100">
      <span class="text-base font-semibold text-slate-900 tabular-nums">
        {{ formatPrice(props.appointment.total_price) }}
      </span>

      <!-- Customer actions: CONFIRMED -->
      <div
        v-if="props.appointment.status === 'CONFIRMED' && props.variant === 'customer'"
        class="flex items-center gap-2"
      >
        <button
          type="button"
          class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="props.loading"
          @click="emit('reschedule', props.appointment)"
        >
          {{ t('appointments.actions.reschedule') }}
        </button>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-red-200 bg-white text-sm font-medium text-red-600 hover:text-red-700 hover:border-red-300 hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="props.loading"
          @click="emit('cancel', props.appointment.id)"
        >
          <span
            v-if="props.loading"
            class="h-3 w-3 border-2 border-red-300 border-t-transparent rounded-full animate-spin"
          />
          {{ t('appointments.actions.cancel') }}
        </button>
      </div>

      <!-- Barber actions: CONFIRMED -->
      <div
        v-else-if="props.appointment.status === 'CONFIRMED' && props.variant === 'barber'"
        class="flex items-center gap-2"
      >
        <button
          type="button"
          class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="props.loading"
          @click="emit('cancel', props.appointment.id)"
        >
          {{ t('appointments.actions.cancel') }}
        </button>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-red-200 bg-white text-sm font-medium text-red-600 hover:text-red-700 hover:border-red-300 hover:bg-red-50 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="props.loading"
          @click="emit('noshow', props.appointment.id)"
        >
          <span
            v-if="props.loading"
            class="h-3 w-3 border-2 border-red-300 border-t-transparent rounded-full animate-spin"
          />
          {{ t('appointments.actions.markNoShow') }}
        </button>
      </div>

      <!-- Review CTA: COMPLETED, customer, no existing review -->
      <RouterLink
        v-else-if="
          props.variant === 'customer' &&
          props.appointment.status === 'COMPLETED' &&
          props.appointment.has_review === false
        "
        :to="`/customer/review/${props.appointment.id}`"
        class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
      >
        <svg class="h-4 w-4 text-amber-400 fill-current" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
        {{ t('appointments.actions.review') }}
      </RouterLink>

      <!-- Rebook CTA: cancelled appointment — let the customer start a new booking with the same barber -->
      <RouterLink
        v-else-if="props.variant === 'customer' && props.appointment.status === 'CANCELLED'"
        :to="`/customer/book/${props.appointment.barber}`"
        class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors"
      >
        Book again
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </RouterLink>
    </div>
  </article>
</template>
