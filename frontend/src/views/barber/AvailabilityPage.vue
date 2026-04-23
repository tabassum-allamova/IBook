<script setup lang="ts">
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import BarberLayout from '@/layouts/BarberLayout.vue'
import WeeklyScheduleEditor from '@/components/availability/WeeklyScheduleEditor.vue'
import DateBlockCalendar from '@/components/availability/DateBlockCalendar.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import type { ScheduleDay } from '@/components/availability/WeeklyScheduleEditor.vue'
import api from '@/lib/axios'

const toast = useToast()
const queryClient = useQueryClient()
const { t } = useI18n()

function defaultSchedule(): ScheduleDay[] {
  return Array.from({ length: 7 }, (_, i) => ({
    day_of_week: i,
    is_working: false,
    start_time: null,
    end_time: null,
    break_start: null,
    break_end: null,
  }))
}

const scheduleData = ref<ScheduleDay[]>(defaultSchedule())
const scheduleError = ref('')

const { data: remoteSchedule, isLoading } = useQuery<ScheduleDay[]>({
  queryKey: ['availability-schedule'],
  queryFn: async () => {
    const res = await api.get<ScheduleDay[]>('/api/availability/schedule/')
    return res.data
  },
})

watch(
  remoteSchedule,
  (data) => {
    if (data && data.length === 7) {
      scheduleData.value = data.map((d) => ({ ...d }))
    }
  },
  { immediate: true },
)

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function validateSchedule(): boolean {
  scheduleError.value = ''
  for (const d of scheduleData.value) {
    if (!d.is_working) continue
    if (!d.start_time || !d.end_time) {
      scheduleError.value = `${DAY_NAMES[d.day_of_week]}: set both start and end times.`
      return false
    }
    if (d.start_time >= d.end_time) {
      scheduleError.value = `${DAY_NAMES[d.day_of_week]}: end time must be after start time.`
      return false
    }
    if (d.break_start || d.break_end) {
      if (!(d.break_start && d.break_end)) {
        scheduleError.value = `${DAY_NAMES[d.day_of_week]}: set both break start and end (or clear both).`
        return false
      }
      if (d.break_start >= d.break_end) {
        scheduleError.value = `${DAY_NAMES[d.day_of_week]}: break end must be after break start.`
        return false
      }
      if (d.break_start < d.start_time || d.break_end > d.end_time) {
        scheduleError.value = `${DAY_NAMES[d.day_of_week]}: break must fall inside working hours.`
        return false
      }
    }
  }
  return true
}

const saveMutation = useMutation({
  mutationFn: async (schedule: ScheduleDay[]) => {
    await api.put('/api/availability/schedule/', schedule)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['availability-schedule'] })
    toast.success(t('availability.saved'))
  },
  onError: () => {
    scheduleError.value = t('toasts.genericError')
    toast.error(t('toasts.genericError'))
  },
})

async function onSaveSchedule() {
  if (!validateSchedule()) return
  await saveMutation.mutateAsync(scheduleData.value)
}
</script>

<template>
  <BarberLayout>
    <section class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="mb-6 md:mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
          {{ t('availability.title') }}
        </h1>
        <p class="mt-1 text-sm text-slate-600">
          {{ t('availability.subtitle') }}
        </p>
      </div>

      <div class="space-y-5 md:space-y-6">
        <!-- Working hours card -->
        <div class="bg-white rounded-xl border border-slate-200 p-6 md:p-8">
          <div class="mb-5">
            <h2 class="text-base font-semibold text-slate-900 tracking-tight">
              {{ t('availability.weeklySchedule') }}
            </h2>
            <p class="mt-0.5 text-sm text-slate-500">
              {{ t('availability.weeklyHint') }}
            </p>
          </div>

          <div v-if="isLoading" class="space-y-3">
            <SkeletonBlock v-for="n in 7" :key="n" height="3rem" />
          </div>
          <template v-else>
            <WeeklyScheduleEditor v-model="scheduleData" />

            <div
              v-if="scheduleError"
              class="mt-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
            >
              {{ scheduleError }}
            </div>

            <div class="pt-5">
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 h-10 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="saveMutation.isPending.value"
                @click="onSaveSchedule"
              >
                <svg
                  v-if="saveMutation.isPending.value"
                  class="h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                  <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                </svg>
                {{ saveMutation.isPending.value ? t('settings.saving') : t('availability.save') }}
              </button>
            </div>
          </template>
        </div>

        <!-- Blocked dates card -->
        <div class="bg-white rounded-xl border border-slate-200 p-6 md:p-8">
          <div class="mb-5">
            <h2 class="text-base font-semibold text-slate-900 tracking-tight">
              {{ t('availability.dateBlocks') }}
            </h2>
            <p class="mt-0.5 text-sm text-slate-500">
              {{ t('availability.dateBlocksHint') }}
            </p>
          </div>
          <DateBlockCalendar />
        </div>
      </div>
    </section>
  </BarberLayout>
</template>
