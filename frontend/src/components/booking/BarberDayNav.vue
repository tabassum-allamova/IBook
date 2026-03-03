<script setup lang="ts">
const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [date: string]
}>()

function formatDisplayDate(dateStr: string): string {
  const date = new Date(dateStr + 'T00:00:00')
  return date.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}

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
</script>

<template>
  <div class="flex items-center justify-center gap-4">
    <!-- Previous day -->
    <button
      type="button"
      class="p-2 rounded-lg text-ibook-brown-600 hover:bg-ibook-brown-100 transition-colors cursor-pointer"
      @click="prevDay"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clip-rule="evenodd" />
      </svg>
    </button>

    <!-- Date display -->
    <div class="text-center">
      <span class="text-sm font-semibold text-ibook-brown-800">
        {{ formatDisplayDate(props.modelValue) }}
      </span>
      <span
        v-if="props.modelValue === todayISO()"
        class="ml-2 text-xs font-medium bg-ibook-gold-400 text-white px-2 py-0.5 rounded-full"
      >
        Today
      </span>
    </div>

    <!-- Next day -->
    <button
      type="button"
      class="p-2 rounded-lg text-ibook-brown-600 hover:bg-ibook-brown-100 transition-colors cursor-pointer"
      @click="nextDay"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
        <path fill-rule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clip-rule="evenodd" />
      </svg>
    </button>

    <!-- Today button (only when not showing today) -->
    <button
      v-if="props.modelValue !== todayISO()"
      type="button"
      class="ml-2 px-3 py-1 text-xs font-medium rounded-lg bg-ibook-gold-400 text-white hover:bg-ibook-gold-500 transition-colors cursor-pointer"
      @click="goToday"
    >
      Today
    </button>
  </div>
</template>
