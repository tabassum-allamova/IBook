<script setup lang="ts">
import { ref, computed } from 'vue'
import { Calendar as VCalendar } from 'v-calendar'
import 'v-calendar/style.css'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import api from '@/lib/axios'

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

// Selected date state
const selectedDate = ref<Date | null>(null)
const blockMode = ref<'none' | 'full' | 'range'>('none')
const blockStart = ref('')
const blockEnd = ref('')
const errorMessage = ref('')

// Find existing block for a date
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
  return date.toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })
}

// Calendar attributes for blocked dates
const calendarAttributes = computed(() => {
  if (!blocks.value) return []
  return blocks.value.map((block) => ({
    key: `block-${block.id}`,
    dates: [new Date(block.date + 'T00:00:00')],
    highlight: 'yellow' as const,
    popover: {
      label: block.block_start
        ? `Blocked: ${block.block_start}–${block.block_end}`
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

function selectTimeRange() {
  blockMode.value = 'range'
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
  <div class="space-y-4">
    <!-- v-calendar -->
    <div class="flex justify-center">
      <VCalendar
        :attributes="calendarAttributes"
        expanded
        borderless
        @dayclick="onDayClick"
      />
    </div>

    <!-- Selected date panel -->
    <div v-if="selectedDate" class="rounded-xl border border-ibook-brown-200 p-4 bg-white space-y-3">
      <div class="flex items-center justify-between">
        <p class="text-sm font-semibold text-ibook-brown-900">{{ formatDate(selectedDate) }}</p>
        <button
          type="button"
          class="text-ibook-brown-400 hover:text-ibook-brown-700 cursor-pointer"
          @click="onCancelSelection"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Existing block: show info + remove -->
      <template v-if="findBlock(selectedDate)">
        <div class="text-sm text-ibook-brown-600 bg-ibook-gold-50 rounded-lg px-3 py-2">
          <span v-if="findBlock(selectedDate)!.block_start">
            Blocked: {{ findBlock(selectedDate)!.block_start }} – {{ findBlock(selectedDate)!.block_end }}
          </span>
          <span v-else>Full day blocked</span>
        </div>
        <button
          type="button"
          :disabled="deleteBlockMutation.isPending.value"
          class="w-full px-4 py-2 rounded-lg border border-red-200 text-red-600 text-sm font-medium hover:bg-red-50 transition-colors disabled:opacity-60 cursor-pointer"
          @click="onRemoveBlock(findBlock(selectedDate)!)"
        >
          {{ deleteBlockMutation.isPending.value ? 'Removing...' : 'Remove Block' }}
        </button>
      </template>

      <!-- No block: offer to create -->
      <template v-else>
        <p class="text-xs text-ibook-brown-500">Choose how to block this date:</p>

        <div class="flex gap-2">
          <button
            type="button"
            :disabled="createBlockMutation.isPending.value"
            class="flex-1 px-3 py-2 rounded-lg bg-ibook-gold-500 text-white text-sm font-medium hover:bg-ibook-gold-600 transition-colors disabled:opacity-60 cursor-pointer"
            @click="onBlockFullDay"
          >
            {{ createBlockMutation.isPending.value && blockMode === 'full' ? 'Blocking...' : 'Block Full Day' }}
          </button>
          <button
            type="button"
            class="flex-1 px-3 py-2 rounded-lg border border-ibook-brown-200 text-ibook-brown-700 text-sm font-medium hover:bg-ibook-brown-50 transition-colors cursor-pointer"
            @click="selectTimeRange"
          >
            Block Time Range
          </button>
        </div>

        <!-- Time range form -->
        <div v-if="blockMode === 'range'" class="space-y-2 pt-1">
          <div class="flex items-center gap-2">
            <label class="text-xs text-ibook-brown-600 w-12 flex-shrink-0">From</label>
            <input
              v-model="blockStart"
              type="time"
              class="flex-1 rounded-lg border border-ibook-brown-200 px-2 py-1.5 text-sm text-ibook-brown-900 focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
            />
          </div>
          <div class="flex items-center gap-2">
            <label class="text-xs text-ibook-brown-600 w-12 flex-shrink-0">To</label>
            <input
              v-model="blockEnd"
              type="time"
              class="flex-1 rounded-lg border border-ibook-brown-200 px-2 py-1.5 text-sm text-ibook-brown-900 focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
            />
          </div>
          <button
            type="button"
            :disabled="createBlockMutation.isPending.value"
            class="w-full px-4 py-2 rounded-lg bg-ibook-gold-500 text-white text-sm font-medium hover:bg-ibook-gold-600 transition-colors disabled:opacity-60 cursor-pointer"
            @click="onBlockTimeRange"
          >
            {{ createBlockMutation.isPending.value ? 'Blocking...' : 'Confirm Block' }}
          </button>
        </div>

        <p v-if="errorMessage" class="text-xs text-red-600">{{ errorMessage }}</p>
      </template>
    </div>

    <!-- No selection hint -->
    <p v-else class="text-xs text-ibook-brown-400 text-center">
      Click a date to mark it as unavailable
    </p>
  </div>
</template>
