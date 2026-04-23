<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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

const dayLabels = computed(() => [
  t('availability.days.mon'),
  t('availability.days.tue'),
  t('availability.days.wed'),
  t('availability.days.thu'),
  t('availability.days.fri'),
  t('availability.days.sat'),
  t('availability.days.sun'),
])

function updateDay(index: number, changes: Partial<ScheduleDay>) {
  const updated = props.modelValue.map((day, i) => {
    if (i !== index) return day
    const merged = { ...day, ...changes }
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

function hasBreak(d: ScheduleDay) {
  return Boolean(d.break_start && d.break_end)
}

function toggleBreak(index: number, enabled: boolean) {
  if (enabled) {
    updateDay(index, { break_start: '13:00', break_end: '14:00' })
  } else {
    updateDay(index, { break_start: null, break_end: null })
  }
}
</script>

<template>
  <ul class="divide-y divide-slate-100">
    <li
      v-for="(label, index) in dayLabels"
      :key="index"
      class="py-4 flex flex-col sm:flex-row sm:items-start gap-3"
    >
      <!-- Toggle + day label -->
      <label class="w-32 flex items-center gap-3 cursor-pointer select-none">
        <input
          type="checkbox"
          :checked="getDay(index).is_working"
          class="h-4 w-4 accent-slate-900"
          @change="updateDay(index, { is_working: ($event.target as HTMLInputElement).checked })"
        />
        <span class="text-sm font-medium text-slate-900">{{ label }}</span>
      </label>

      <div class="flex-1 space-y-2">
        <!-- Working hours -->
        <div v-if="getDay(index).is_working" class="flex flex-wrap items-center gap-2 text-sm text-slate-700">
          <input
            type="time"
            :value="getDay(index).start_time ?? ''"
            class="h-9 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
            @change="updateDay(index, { start_time: ($event.target as HTMLInputElement).value || null })"
          />
          <span class="text-slate-400">–</span>
          <input
            type="time"
            :value="getDay(index).end_time ?? ''"
            class="h-9 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
            @change="updateDay(index, { end_time: ($event.target as HTMLInputElement).value || null })"
          />

          <label class="inline-flex items-center gap-2 ml-3 text-sm text-slate-700 cursor-pointer select-none">
            <input
              type="checkbox"
              :checked="hasBreak(getDay(index))"
              class="h-4 w-4 accent-slate-900"
              @change="toggleBreak(index, ($event.target as HTMLInputElement).checked)"
            />
            {{ t('availability.break') }}
          </label>

          <template v-if="hasBreak(getDay(index))">
            <input
              type="time"
              :value="getDay(index).break_start ?? ''"
              class="h-9 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
              @change="updateDay(index, { break_start: ($event.target as HTMLInputElement).value || null })"
            />
            <span class="text-slate-400">–</span>
            <input
              type="time"
              :value="getDay(index).break_end ?? ''"
              class="h-9 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
              @change="updateDay(index, { break_end: ($event.target as HTMLInputElement).value || null })"
            />
          </template>
        </div>

        <p v-else class="text-sm text-slate-400">{{ t('availability.dayOff') }}</p>
      </div>
    </li>
  </ul>
</template>
