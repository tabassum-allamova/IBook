<script setup lang="ts">
export interface ScheduleDay {
  day_of_week: number // 0=Mon, 6=Sun
  is_working: boolean
  start_time: string | null // 'HH:MM'
  end_time: string | null
  break_start: string | null
  break_end: string | null
}

const props = defineProps<{
  modelValue: ScheduleDay[]
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ScheduleDay[]]
}>()

const dayLabels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function updateDay(index: number, changes: Partial<ScheduleDay>) {
  const updated = props.modelValue.map((day, i) => {
    if (i !== index) return day
    const merged = { ...day, ...changes }
    // Clear time fields when toggled off
    if ('is_working' in changes && !changes.is_working) {
      merged.start_time = null
      merged.end_time = null
      merged.break_start = null
      merged.break_end = null
    }
    return merged
  })
  emit('update:modelValue', updated)
}

function getDay(index: number): ScheduleDay {
  return (
    props.modelValue[index] ?? {
      day_of_week: index,
      is_working: false,
      start_time: null,
      end_time: null,
      break_start: null,
      break_end: null,
    }
  )
}
</script>

<template>
  <div class="space-y-2">
    <div
      v-for="(label, index) in dayLabels"
      :key="index"
      class="flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl px-4 py-3 transition-colors"
      :class="getDay(index).is_working ? 'bg-white border border-ibook-brown-100' : 'bg-ibook-cream border border-ibook-brown-100'"
    >
      <!-- Toggle + Day label -->
      <div class="flex items-center gap-3 w-36 flex-shrink-0">
        <input
          :id="`day-toggle-${index}`"
          type="checkbox"
          :checked="getDay(index).is_working"
          class="w-4 h-4 accent-ibook-gold-500 cursor-pointer"
          @change="updateDay(index, { is_working: ($event.target as HTMLInputElement).checked })"
        />
        <label
          :for="`day-toggle-${index}`"
          class="text-sm font-medium cursor-pointer"
          :class="getDay(index).is_working ? 'text-ibook-brown-900' : 'text-ibook-brown-500'"
        >
          {{ label }}
        </label>
      </div>

      <!-- Closed indicator -->
      <span v-if="!getDay(index).is_working" class="text-sm text-ibook-brown-400 italic">
        Closed
      </span>

      <!-- Working hours -->
      <template v-if="getDay(index).is_working">
        <div class="flex items-center gap-2">
          <input
            type="time"
            :value="getDay(index).start_time ?? ''"
            class="rounded-lg border border-ibook-brown-200 px-2 py-1.5 text-sm text-ibook-brown-900 focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
            @change="updateDay(index, { start_time: ($event.target as HTMLInputElement).value || null })"
          />
          <span class="text-ibook-brown-400 font-medium">–</span>
          <input
            type="time"
            :value="getDay(index).end_time ?? ''"
            class="rounded-lg border border-ibook-brown-200 px-2 py-1.5 text-sm text-ibook-brown-900 focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
            @change="updateDay(index, { end_time: ($event.target as HTMLInputElement).value || null })"
          />
        </div>

        <!-- Break times -->
        <div class="flex items-center gap-2 text-sm text-ibook-brown-500">
          <span class="flex-shrink-0">Break:</span>
          <input
            type="time"
            :value="getDay(index).break_start ?? ''"
            class="rounded-lg border border-ibook-brown-200 px-2 py-1.5 text-sm text-ibook-brown-900 focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
            @change="updateDay(index, { break_start: ($event.target as HTMLInputElement).value || null })"
          />
          <span class="text-ibook-brown-400 font-medium">–</span>
          <input
            type="time"
            :value="getDay(index).break_end ?? ''"
            class="rounded-lg border border-ibook-brown-200 px-2 py-1.5 text-sm text-ibook-brown-900 focus:outline-none focus:ring-2 focus:ring-ibook-gold-400"
            @change="updateDay(index, { break_end: ($event.target as HTMLInputElement).value || null })"
          />
        </div>
      </template>
    </div>
  </div>
</template>
