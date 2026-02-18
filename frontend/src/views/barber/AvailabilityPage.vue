<script setup lang="ts">
import { ref, watch } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import BarberLayout from '@/layouts/BarberLayout.vue'
import WeeklyScheduleEditor from '@/components/availability/WeeklyScheduleEditor.vue'
import DateBlockCalendar from '@/components/availability/DateBlockCalendar.vue'
import type { ScheduleDay } from '@/components/availability/WeeklyScheduleEditor.vue'
import api from '@/lib/axios'

const queryClient = useQueryClient()

// Default 7-day schedule (all closed)
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
const saveSuccess = ref(false)
const saveError = ref('')

const { data: remoteSchedule, isLoading } = useQuery<ScheduleDay[]>({
  queryKey: ['availability-schedule'],
  queryFn: async () => {
    const res = await api.get<ScheduleDay[]>('/api/availability/schedule/')
    return res.data
  },
})

// Sync loaded schedule into local state
watch(
  remoteSchedule,
  (data) => {
    if (data && data.length === 7) {
      scheduleData.value = data.map((d) => ({ ...d }))
    }
  },
  { immediate: true },
)

const saveMutation = useMutation({
  mutationFn: async (schedule: ScheduleDay[]) => {
    await api.put('/api/availability/schedule/', schedule)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['availability-schedule'] })
    saveSuccess.value = true
    saveError.value = ''
    setTimeout(() => {
      saveSuccess.value = false
    }, 3000)
  },
  onError: () => {
    saveError.value = 'Failed to save schedule. Please try again.'
    saveSuccess.value = false
  },
})

async function onSaveSchedule() {
  await saveMutation.mutateAsync(scheduleData.value)
}
</script>

<template>
  <BarberLayout>
    <div class="p-8 space-y-6">
      <!-- Page header -->
      <div>
        <h1 class="text-3xl font-bold text-ibook-brown-900">Availability</h1>
        <p class="mt-1 text-ibook-brown-500">Set your working hours and block off unavailable dates.</p>
      </div>

      <!-- Section 1: Working Hours -->
      <div class="bg-ibook-brown-50 rounded-2xl shadow-sm p-6">
        <div class="flex items-start justify-between mb-6">
          <div>
            <h2 class="text-xl font-semibold text-ibook-brown-700">Working Hours</h2>
            <p class="text-sm text-ibook-brown-500 mt-0.5">Toggle each day and set your working times.</p>
          </div>
        </div>

        <div v-if="isLoading" class="py-6 text-center text-ibook-brown-400 text-sm">
          Loading schedule...
        </div>
        <div v-else class="space-y-4">
          <WeeklyScheduleEditor v-model="scheduleData" />

          <div class="flex items-center gap-4 pt-2">
            <button
              type="button"
              :disabled="saveMutation.isPending.value"
              class="px-6 py-2.5 rounded-xl bg-ibook-gold-500 text-white text-sm font-semibold hover:bg-ibook-gold-600 transition-colors disabled:opacity-60 shadow-sm cursor-pointer"
              @click="onSaveSchedule"
            >
              {{ saveMutation.isPending.value ? 'Saving...' : 'Save Schedule' }}
            </button>
            <span v-if="saveSuccess" class="text-sm text-green-600 font-medium">Schedule saved</span>
            <span v-if="saveError" class="text-sm text-red-600">{{ saveError }}</span>
          </div>
        </div>
      </div>

      <!-- Section 2: Blocked Dates -->
      <div class="bg-ibook-brown-50 rounded-2xl shadow-sm p-6">
        <div class="mb-6">
          <h2 class="text-xl font-semibold text-ibook-brown-700">Blocked Dates</h2>
          <p class="text-sm text-ibook-brown-500 mt-0.5">Click a date to mark it as unavailable.</p>
        </div>
        <DateBlockCalendar />
      </div>
    </div>
  </BarberLayout>
</template>
