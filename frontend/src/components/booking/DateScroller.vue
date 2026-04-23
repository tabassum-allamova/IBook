<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'

const props = defineProps<{
  selected: string
}>()

const emit = defineEmits<{
  select: [dateIso: string]
}>()

interface DateEntry {
  iso: string
  dayName: string
  dayNum: number
  month: string
  monthLong: string
  isFirstOfMonth: boolean
}

const dates = computed<DateEntry[]>(() => {
  const result: DateEntry[] = []
  const today = new Date()
  for (let i = 0; i < 14; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() + i)
    const prev = result[result.length - 1]
    const monthShort = d.toLocaleDateString('en-US', { month: 'short' })
    result.push({
      iso: d.toISOString().split('T')[0],
      dayName: d.toLocaleDateString('en-US', { weekday: 'short' }),
      dayNum: d.getDate(),
      month: monthShort,
      monthLong: d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
      isFirstOfMonth: !prev || prev.month !== monthShort,
    })
  }
  return result
})

const monthRange = computed(() => {
  const first = dates.value[0]
  const last = dates.value[dates.value.length - 1]
  if (!first || !last) return ''
  if (first.month === last.month) return first.monthLong
  return `${first.month} – ${last.monthLong}`
})

const scrollEl = ref<HTMLDivElement | null>(null)

function scrollBy(delta: number) {
  scrollEl.value?.scrollBy({ left: delta, behavior: 'smooth' })
}

onMounted(() => {
  if (!scrollEl.value) return
  const selectedBtn = scrollEl.value.querySelector<HTMLButtonElement>(
    `[data-iso="${props.selected}"]`,
  )
  selectedBtn?.scrollIntoView({ behavior: 'instant', inline: 'center', block: 'nearest' })
})
</script>

<template>
  <div>
    <!-- Month + arrows -->
    <div class="flex items-center justify-between mb-3">
      <p class="text-sm font-medium text-slate-700">{{ monthRange }}</p>
      <div class="hidden sm:flex items-center gap-1">
        <button
          type="button"
          aria-label="Scroll earlier"
          class="h-8 w-8 inline-flex items-center justify-center rounded-md border border-slate-200 text-slate-500 hover:text-slate-900 hover:border-slate-400 transition-colors"
          @click="scrollBy(-220)"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <button
          type="button"
          aria-label="Scroll later"
          class="h-8 w-8 inline-flex items-center justify-center rounded-md border border-slate-200 text-slate-500 hover:text-slate-900 hover:border-slate-400 transition-colors"
          @click="scrollBy(220)"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Tiles -->
    <div
      ref="scrollEl"
      class="scroll flex gap-2 pb-1 overflow-x-auto snap-x"
      style="-ms-overflow-style: none; scrollbar-width: none"
    >
      <button
        v-for="d in dates"
        :key="d.iso"
        :data-iso="d.iso"
        type="button"
        class="shrink-0 snap-start flex flex-col items-center justify-center w-14 h-[4.5rem] rounded-xl transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
        :class="
          d.iso === props.selected
            ? 'bg-slate-900 text-white'
            : 'bg-white text-slate-700 border border-slate-200 hover:border-slate-400'
        "
        @click="emit('select', d.iso)"
      >
        <span
          class="text-sm font-medium"
          :class="d.iso === props.selected ? 'text-slate-300' : 'text-slate-500'"
        >
          {{ d.dayName }}
        </span>
        <span class="text-xl font-semibold leading-none tabular-nums mt-1">
          {{ d.dayNum }}
        </span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.scroll::-webkit-scrollbar {
  display: none;
}
</style>
