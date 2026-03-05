<script setup lang="ts">
import { computed } from 'vue'

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
}

const dates = computed<DateEntry[]>(() => {
  const result: DateEntry[] = []
  const today = new Date()
  for (let i = 0; i < 14; i++) {
    const d = new Date(today)
    d.setDate(today.getDate() + i)
    result.push({
      iso: d.toISOString().split('T')[0],
      dayName: d.toLocaleDateString('en-US', { weekday: 'short' }),
      dayNum: d.getDate(),
      month: d.toLocaleDateString('en-US', { month: 'short' }),
    })
  }
  return result
})
</script>

<template>
  <div
    class="flex gap-2 pb-2 overflow-x-auto"
    style="-ms-overflow-style: none; scrollbar-width: none"
  >
    <button
      v-for="d in dates"
      :key="d.iso"
      type="button"
      class="shrink-0 flex flex-col items-center w-16 py-2 rounded-xl transition-colors cursor-pointer"
      :class="
        d.iso === props.selected
          ? 'bg-ibook-brown-800 text-white'
          : 'bg-white text-ibook-brown-700 border border-ibook-brown-200 hover:border-ibook-brown-400'
      "
      @click="emit('select', d.iso)"
    >
      <span class="text-xs uppercase">{{ d.dayName }}</span>
      <span class="text-lg font-bold leading-tight">{{ d.dayNum }}</span>
      <span class="text-xs">{{ d.month }}</span>
    </button>
  </div>
</template>

<style scoped>
div::-webkit-scrollbar {
  display: none;
}
</style>
