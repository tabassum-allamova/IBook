<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import BarberLayout from '@/layouts/BarberLayout.vue'
import BarberDayNav from '@/components/booking/BarberDayNav.vue'
import AppointmentCard from '@/components/booking/AppointmentCard.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import type { AppointmentData } from '@/components/booking/AppointmentCard.vue'
import api from '@/lib/axios'

const toast = useToast()
const queryClient = useQueryClient()
const { t } = useI18n()

function todayISO(): string {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}

const selectedDate = ref(todayISO())

const { data: appointments, isLoading } = useQuery<AppointmentData[]>({
  queryKey: computed(() => ['barber-appointments', selectedDate.value]),
  queryFn: () =>
    api
      .get<AppointmentData[]>('/api/bookings/barber/day/', {
        params: { date: selectedDate.value },
      })
      .then((r) => r.data),
})

const appointmentCount = computed(() => appointments.value?.length ?? 0)

const dayRevenue = computed(() => {
  if (!appointments.value) return 0
  return appointments.value
    .filter((a) => a.status === 'CONFIRMED' || a.status === 'COMPLETED')
    .reduce((sum, a) => sum + a.total_price, 0)
})

// ---- Status tabs ----
type StatusFilter = 'all' | 'upcoming' | 'completed' | 'cancelled' | 'no_show'

const statusFilter = ref<StatusFilter>('all')

const tabs: Array<{ id: StatusFilter; label: string }> = [
  { id: 'all', label: 'All' },
  { id: 'upcoming', label: 'Upcoming' },
  { id: 'completed', label: 'Completed' },
  { id: 'cancelled', label: 'Cancelled' },
  { id: 'no_show', label: 'No-show' },
]

const countsByStatus = computed<Record<StatusFilter, number>>(() => {
  const appts = appointments.value ?? []
  return {
    all: appts.length,
    upcoming: appts.filter((a) => a.status === 'CONFIRMED').length,
    completed: appts.filter((a) => a.status === 'COMPLETED').length,
    cancelled: appts.filter((a) => a.status === 'CANCELLED').length,
    no_show: appts.filter((a) => a.status === 'NO_SHOW').length,
  }
})

const filteredAppointments = computed(() => {
  const appts = appointments.value ?? []
  switch (statusFilter.value) {
    case 'all':
      return appts
    case 'upcoming':
      return appts.filter((a) => a.status === 'CONFIRMED')
    case 'completed':
      return appts.filter((a) => a.status === 'COMPLETED')
    case 'cancelled':
      return appts.filter((a) => a.status === 'CANCELLED')
    case 'no_show':
      return appts.filter((a) => a.status === 'NO_SHOW')
  }
})

const activeTabLabel = computed(
  () => tabs.find((t) => t.id === statusFilter.value)?.label.toLowerCase() ?? '',
)

function formatPrice(price: number): string {
  return price.toLocaleString('en-US') + ' UZS'
}

// ---- Confirmation modal ----
type PendingAction =
  | { type: 'cancel'; appointment: AppointmentData }
  | { type: 'noshow'; appointment: AppointmentData }
  | null

const pending = ref<PendingAction>(null)
const isConfirming = ref(false)

const modal = computed(() => {
  if (!pending.value) return null
  if (pending.value.type === 'cancel') {
    return {
      title: t('barberAppointments.cancelTitle'),
      body: t('barberAppointments.cancelBody'),
      confirmLabel: t('barberAppointments.cancelConfirm'),
      keepLabel: t('barberAppointments.cancelKeep'),
    }
  }
  return {
    title: t('barberAppointments.noShowTitle'),
    body: t('barberAppointments.noShowBody'),
    confirmLabel: t('barberAppointments.noShowConfirm'),
    keepLabel: t('barberAppointments.noShowKeep'),
  }
})

function requestCancel(id: number) {
  const appt = appointments.value?.find((a) => a.id === id)
  if (appt) pending.value = { type: 'cancel', appointment: appt }
}

function requestNoShow(id: number) {
  const appt = appointments.value?.find((a) => a.id === id)
  if (appt) pending.value = { type: 'noshow', appointment: appt }
}

function closeModal() {
  if (isConfirming.value) return
  pending.value = null
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && pending.value && !isConfirming.value) closeModal()
}

watch(pending, (p) => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = p ? 'hidden' : ''
  if (p) window.addEventListener('keydown', onKeydown)
  else window.removeEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (typeof document !== 'undefined') document.body.style.overflow = ''
})

// ---- Mutations ----
const cancelMutation = useMutation({
  mutationFn: (appointmentId: number) =>
    api.post(`/api/bookings/${appointmentId}/cancel/`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['barber-appointments'] })
    toast.success(t('barberAppointments.cancelled'))
  },
  onError: () => {
    toast.error(t('barberAppointments.cancelFailed'))
  },
})

const noShowMutation = useMutation({
  mutationFn: (appointmentId: number) =>
    api.post(`/api/bookings/${appointmentId}/no-show/`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['barber-appointments'] })
    toast.success(t('barberAppointments.noShowMarked'))
  },
  onError: () => {
    toast.error(t('barberAppointments.noShowFailed'))
  },
})

async function confirmAction() {
  if (!pending.value) return
  const action = pending.value
  isConfirming.value = true
  try {
    if (action.type === 'cancel') {
      await cancelMutation.mutateAsync(action.appointment.id)
    } else {
      await noShowMutation.mutateAsync(action.appointment.id)
    }
    pending.value = null
  } finally {
    isConfirming.value = false
  }
}
</script>

<template>
  <BarberLayout>
    <section class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
            {{ t('barberAppointments.title') }}
          </h1>
          <p class="mt-1 text-sm text-slate-600">
            {{ t('barberAppointments.subtitle') }}
          </p>
        </div>

        <BarberDayNav v-model="selectedDate" />
      </div>

      <!-- Day summary -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5 mb-5 md:mb-6">
        <div class="bg-white rounded-xl border border-slate-200 p-6">
          <p class="text-sm font-medium text-slate-500 mb-2">{{ t('barberAppointments.dayAppointments') }}</p>
          <p class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight tabular-nums">
            {{ appointmentCount }}
          </p>
          <p class="mt-2 text-sm text-slate-500">{{ t('barberAppointments.forThisDay') }}</p>
        </div>
        <div class="bg-white rounded-xl border border-slate-200 p-6">
          <p class="text-sm font-medium text-slate-500 mb-2">{{ t('barberAppointments.dayRevenue') }}</p>
          <p class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight tabular-nums">
            {{ formatPrice(dayRevenue) }}
          </p>
          <p class="mt-2 text-sm text-slate-500">{{ t('barberAppointments.confirmedCompleted') }}</p>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="space-y-3">
        <SkeletonBlock v-for="n in 3" :key="n" height="8rem" />
      </div>

      <!-- Empty state: no appointments at all for this day -->
      <div
        v-else-if="!appointments || appointments.length === 0"
        class="bg-white rounded-xl border border-slate-200 p-12 flex flex-col items-center text-center"
      >
        <div class="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center mb-4">
          <svg class="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 00-2 2z" />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-slate-900 tracking-tight mb-1">
          {{ t('barberAppointments.empty') }}
        </h3>
        <p class="text-sm text-slate-500 max-w-xs leading-relaxed">
          {{ t('barberAppointments.emptyDesc') }}
        </p>
      </div>

      <!-- Day has appointments: show tabs + filtered list -->
      <template v-else>
        <div class="border-b border-slate-200 mb-5">
          <nav
            role="tablist"
            aria-label="Filter by status"
            class="flex items-center gap-1 overflow-x-auto -mb-px"
          >
            <button
              v-for="t in tabs"
              :key="t.id"
              role="tab"
              type="button"
              :aria-selected="statusFilter === t.id"
              :class="[
                'inline-flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap focus:outline-none focus-visible:text-slate-900',
                statusFilter === t.id
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-900',
              ]"
              @click="statusFilter = t.id"
            >
              {{ t.label }}
              <span
                :class="[
                  'inline-flex items-center justify-center min-w-[1.5rem] h-5 px-1.5 rounded-full text-sm font-medium tabular-nums transition-colors',
                  statusFilter === t.id
                    ? 'bg-slate-900 text-white'
                    : 'bg-slate-100 text-slate-600',
                ]"
              >
                {{ countsByStatus[t.id] }}
              </span>
            </button>
          </nav>
        </div>

        <!-- Filtered list -->
        <div v-if="filteredAppointments.length > 0" class="space-y-3">
          <AppointmentCard
            v-for="appt in filteredAppointments"
            :key="appt.id"
            :appointment="appt"
            variant="barber"
            :loading="pending?.appointment.id === appt.id && isConfirming"
            @noshow="requestNoShow"
            @cancel="requestCancel"
          />
        </div>

        <!-- Empty state for the selected tab -->
        <div
          v-else
          class="bg-white rounded-xl border border-slate-200 p-10 flex flex-col items-center text-center"
        >
          <div class="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center mb-4">
            <svg class="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5M12 17.25h8.25" />
            </svg>
          </div>
          <h3 class="text-base font-semibold text-slate-900 tracking-tight mb-1">
            {{ t('barberAppointments.emptyTab', { tab: activeTabLabel }) }}
          </h3>
          <p class="text-sm text-slate-500 max-w-xs leading-relaxed">
            {{ t('barberAppointments.emptyTabHint') }}
          </p>
        </div>
      </template>

      <!-- Confirm modal -->
      <Teleport to="body">
        <Transition name="fade">
          <div
            v-if="pending && modal"
            class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-end md:items-center justify-center md:p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="barber-confirm-title"
            @click.self="closeModal"
          >
            <Transition name="slide-up">
              <div
                v-if="pending"
                class="w-full md:max-w-md bg-white rounded-t-2xl md:rounded-2xl shadow-xl p-5 md:p-6"
              >
                <h2 id="barber-confirm-title" class="text-lg font-semibold text-slate-900 tracking-tight">
                  {{ modal.title }}
                </h2>
                <p class="mt-2 text-sm text-slate-600 leading-relaxed">
                  {{ modal.body }}
                </p>

                <!-- Appointment recap -->
                <div class="mt-4 rounded-lg bg-slate-50 border border-slate-100 px-4 py-3">
                  <p class="text-sm text-slate-900 font-medium">
                    {{
                      new Date(pending.appointment.date + 'T00:00:00').toLocaleDateString('en-US', {
                        weekday: 'short',
                        month: 'short',
                        day: 'numeric',
                      })
                    }}
                    ·
                    <span class="tabular-nums">
                      {{ pending.appointment.start_time.slice(0, 5) }} – {{ pending.appointment.end_time.slice(0, 5) }}
                    </span>
                  </p>
                  <p v-if="pending.appointment.customer_name" class="mt-0.5 text-sm text-slate-500">
                    with {{ pending.appointment.customer_name }}
                  </p>
                </div>

                <div class="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end gap-2">
                  <button
                    type="button"
                    class="inline-flex items-center justify-center h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="isConfirming"
                    @click="closeModal"
                  >
                    {{ modal.keepLabel }}
                  </button>
                  <button
                    type="button"
                    class="inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                    :disabled="isConfirming"
                    @click="confirmAction"
                  >
                    <svg
                      v-if="isConfirming"
                      class="h-4 w-4 animate-spin"
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                      <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                    </svg>
                    {{ modal.confirmLabel }}
                  </button>
                </div>
              </div>
            </Transition>
          </div>
        </Transition>
      </Teleport>
    </section>
  </BarberLayout>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.18s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(16px);
  opacity: 0;
}
@media (min-width: 768px) {
  .slide-up-enter-from,
  .slide-up-leave-to {
    transform: scale(0.97);
  }
}
</style>
