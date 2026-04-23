<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Calendar as VCalendar } from 'v-calendar'
import 'v-calendar/style.css'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import api from '@/lib/axios'

const { t, locale } = useI18n()

const BROWSER_LOCALES: Record<string, string> = {
  en: 'en-US',
  ru: 'ru-RU',
  uz: 'uz-UZ',
}

interface DateBlock {
  id: number
  date: string // 'YYYY-MM-DD'
  block_start: string | null // 'HH:MM'
  block_end: string | null
}

const queryClient = useQueryClient()

const { data: blocks } = useQuery<DateBlock[]>({
  queryKey: ['availability-blocks'],
  queryFn: async () => {
    const res = await api.get<DateBlock[]>('/api/availability/blocks/')
    return res.data
  },
})

const selectedDate = ref<Date | null>(null)
const blockMode = ref<'none' | 'range'>('none')
const blockStart = ref('')
const blockEnd = ref('')
const errorMessage = ref('')

function findBlock(date: Date): DateBlock | undefined {
  if (!blocks.value) return undefined
  const dateStr = toDateString(date)
  return blocks.value.find((b) => b.date === dateStr)
}

function toDateString(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function formatDate(date: Date): string {
  const tag = BROWSER_LOCALES[locale.value] ?? 'en-US'
  return date.toLocaleDateString(tag, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

const calendarAttributes = computed(() => {
  if (!blocks.value) return []
  return blocks.value.map((block) => ({
    key: `block-${block.id}`,
    dates: [new Date(block.date + 'T00:00:00')],
    highlight: { color: 'gray' as const, fillMode: 'solid' as const },
    popover: {
      label: block.block_start
        ? `Blocked ${block.block_start}–${block.block_end}`
        : 'Full day blocked',
    },
  }))
})

function onDayClick({ date }: { date: Date }) {
  selectedDate.value = date
  blockMode.value = 'none'
  blockStart.value = ''
  blockEnd.value = ''
  errorMessage.value = ''
}

const createBlockMutation = useMutation({
  mutationFn: async (payload: { date: string; block_start?: string; block_end?: string }) => {
    await api.post('/api/availability/blocks/', payload)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['availability-blocks'] })
    selectedDate.value = null
    blockMode.value = 'none'
    blockStart.value = ''
    blockEnd.value = ''
    errorMessage.value = ''
  },
  onError: () => {
    errorMessage.value = 'Failed to block date. Please try again.'
  },
})

const deleteBlockMutation = useMutation({
  mutationFn: async (blockId: number) => {
    await api.delete(`/api/availability/blocks/${blockId}/`)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['availability-blocks'] })
    selectedDate.value = null
    blockMode.value = 'none'
    errorMessage.value = ''
  },
  onError: () => {
    errorMessage.value = 'Failed to remove block. Please try again.'
  },
})

async function onBlockFullDay() {
  if (!selectedDate.value) return
  await createBlockMutation.mutateAsync({ date: toDateString(selectedDate.value) })
}

async function onBlockTimeRange() {
  if (!selectedDate.value) return
  if (!blockStart.value || !blockEnd.value) {
    errorMessage.value = 'Please enter both start and end times.'
    return
  }
  if (blockStart.value >= blockEnd.value) {
    errorMessage.value = 'End time must be after start time.'
    return
  }
  await createBlockMutation.mutateAsync({
    date: toDateString(selectedDate.value),
    block_start: blockStart.value,
    block_end: blockEnd.value,
  })
}

async function onRemoveBlock(block: DateBlock) {
  await deleteBlockMutation.mutateAsync(block.id)
}

function onCancelSelection() {
  selectedDate.value = null
  blockMode.value = 'none'
  errorMessage.value = ''
}
</script>

<template>
  <div class="grid md:grid-cols-[1fr_320px] gap-5">
    <!-- Calendar -->
    <div class="vc-host">
      <VCalendar
        :attributes="calendarAttributes"
        expanded
        borderless
        @dayclick="onDayClick"
      />
    </div>

    <!-- Selection panel -->
    <aside>
      <div
        v-if="selectedDate"
        class="rounded-xl border border-slate-200 bg-slate-50/60 p-5"
      >
        <div class="flex items-center justify-between mb-3">
          <p class="text-sm font-semibold text-slate-900">{{ formatDate(selectedDate) }}</p>
          <button
            type="button"
            aria-label="Clear selection"
            class="inline-flex items-center justify-center h-8 w-8 rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            @click="onCancelSelection"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Existing block -->
        <template v-if="findBlock(selectedDate)">
          <div class="rounded-lg bg-white border border-slate-200 px-3 py-2.5 text-sm text-slate-700">
            <span v-if="findBlock(selectedDate)!.block_start">
              {{ t('availability.blocked') }} <span class="tabular-nums font-medium text-slate-900">
                {{ findBlock(selectedDate)!.block_start }} – {{ findBlock(selectedDate)!.block_end }}
              </span>
            </span>
            <span v-else>{{ t('availability.blockFullDay') }}</span>
          </div>
          <button
            type="button"
            :disabled="deleteBlockMutation.isPending.value"
            class="mt-3 w-full inline-flex items-center justify-center gap-1.5 h-10 px-4 rounded-lg border border-red-200 bg-white text-sm font-medium text-red-600 hover:text-red-700 hover:border-red-300 hover:bg-red-50 transition-colors disabled:opacity-60"
            @click="onRemoveBlock(findBlock(selectedDate)!)"
          >
            <svg
              v-if="deleteBlockMutation.isPending.value"
              class="h-4 w-4 animate-spin"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
              <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
            </svg>
            {{ deleteBlockMutation.isPending.value ? t('common.loading') : t('availability.unblock') }}
          </button>
        </template>

        <!-- No block: create -->
        <template v-else>
          <p class="text-sm text-slate-500 mb-3">{{ t('availability.pickDate') }}</p>

          <div class="flex gap-2">
            <button
              type="button"
              :disabled="createBlockMutation.isPending.value"
              class="flex-1 inline-flex items-center justify-center h-10 px-3 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors disabled:opacity-60"
              @click="onBlockFullDay"
            >
              {{ t('availability.fullDay') }}
            </button>
            <button
              type="button"
              class="flex-1 inline-flex items-center justify-center h-10 px-3 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors"
              @click="blockMode = 'range'"
            >
              {{ t('availability.hoursOnly') }}
            </button>
          </div>

          <!-- Range form -->
          <div v-if="blockMode === 'range'" class="mt-3 space-y-2">
            <div class="flex items-center gap-2">
              <span class="w-12 text-sm text-slate-500 flex-shrink-0">{{ t('availability.blockFrom') }}</span>
              <input
                v-model="blockStart"
                type="time"
                class="flex-1 h-10 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
              />
            </div>
            <div class="flex items-center gap-2">
              <span class="w-12 text-sm text-slate-500 flex-shrink-0">{{ t('availability.blockTo') }}</span>
              <input
                v-model="blockEnd"
                type="time"
                class="flex-1 h-10 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
              />
            </div>
            <button
              type="button"
              :disabled="createBlockMutation.isPending.value"
              class="mt-1 w-full inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors disabled:opacity-60"
              @click="onBlockTimeRange"
            >
              <svg
                v-if="createBlockMutation.isPending.value"
                class="h-4 w-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
              </svg>
              {{ createBlockMutation.isPending.value ? t('common.loading') : t('availability.saveBlock') }}
            </button>
          </div>

          <p v-if="errorMessage" class="mt-3 text-sm text-red-600">{{ errorMessage }}</p>
        </template>
      </div>

      <div
        v-else
        class="rounded-xl border border-dashed border-slate-200 bg-white p-6 text-center"
      >
        <p class="text-sm font-medium text-slate-900">{{ t('availability.pickDate') }}</p>
        <p class="mt-1 text-sm text-slate-500">
          {{ t('availability.pickDateHint') }}
        </p>
      </div>
    </aside>
  </div>
</template>

<style scoped>
/* Tone v-calendar down into the slate palette. */
.vc-host :deep(.vc-container) {
  --vc-accent-50: rgb(241 245 249);
  --vc-accent-100: rgb(226 232 240);
  --vc-accent-200: rgb(203 213 225);
  --vc-accent-300: rgb(148 163 184);
  --vc-accent-400: rgb(100 116 139);
  --vc-accent-500: rgb(15 23 42);
  --vc-accent-600: rgb(15 23 42);
  --vc-accent-700: rgb(30 41 59);
  --vc-accent-800: rgb(30 41 59);
  --vc-accent-900: rgb(15 23 42);
  --vc-rounded-full: 0.5rem;
  border-radius: 0.75rem;
  font-family: inherit;
}
</style>
