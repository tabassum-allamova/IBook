<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t, locale } = useI18n()

const BROWSER_LOCALES: Record<string, string> = {
  en: 'en-US',
  ru: 'ru-RU',
  uz: 'uz-UZ',
}

const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [date: string]
}>()

function todayISO(): string {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

function addDays(dateStr: string, days: number): string {
  const d = new Date(dateStr + 'T00:00:00')
  d.setDate(d.getDate() + days)
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

function prevDay() {
  emit('update:modelValue', addDays(props.modelValue, -1))
}

function nextDay() {
  emit('update:modelValue', addDays(props.modelValue, 1))
}

function goToday() {
  emit('update:modelValue', todayISO())
}

const label = computed(() => {
  const date = new Date(props.modelValue + 'T00:00:00')
  const tag = BROWSER_LOCALES[locale.value] ?? 'en-US'
  return date.toLocaleDateString(tag, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
})

const isToday = computed(() => props.modelValue === todayISO())
</script>

<template>
  <div class="flex items-center gap-3">
    <div class="inline-flex items-center rounded-lg border border-slate-200 bg-white">
      <button
        type="button"
        aria-label="Previous day"
        class="inline-flex items-center justify-center h-10 w-10 text-slate-500 hover:text-slate-900 transition-colors"
        @click="prevDay"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      <div class="px-3 min-w-[12rem] flex items-center justify-center gap-2 border-x border-slate-200 h-10">
        <span class="text-sm font-medium text-slate-900 whitespace-nowrap">{{ label }}</span>
        <span
          v-if="isToday"
          class="inline-flex items-center px-1.5 py-0.5 rounded-md text-sm font-medium bg-slate-100 text-slate-700"
        >
          {{ t('booking.dayNav.today') }}
        </span>
      </div>

      <button
        type="button"
        aria-label="Next day"
        class="inline-flex items-center justify-center h-10 w-10 text-slate-500 hover:text-slate-900 transition-colors"
        @click="nextDay"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </button>
    </div>

    <button
      v-if="!isToday"
      type="button"
      class="inline-flex items-center h-10 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors"
      @click="goToday"
    >
      {{ t('booking.dayNav.today') }}
    </button>
  </div>
</template>
