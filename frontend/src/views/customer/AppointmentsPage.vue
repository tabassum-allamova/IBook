<script setup lang="ts">
import { ref, computed, watch, onUnmounted, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import AppointmentCard from '@/components/booking/AppointmentCard.vue'
import SkeletonBlock from '@/components/ui/SkeletonBlock.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import type { AppointmentData } from '@/components/booking/AppointmentCard.vue'
import api from '@/lib/axios'

const toast = useToast()
const { t } = useI18n()

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()

type Tab = 'upcoming' | 'past'
const activeTab = ref<Tab>('upcoming')

// Session IDs already consumed by finalize — guards against a second POST
// when the user navigates back to this page with the same `?session_id=` in
// the URL (e.g. browser back/forward, bookmark) before router.replace strips
// the query. Per-session because there's no reason to re-try a successful one.
const finalizedSessions = new Set<string>()

// When the customer returns from Stripe, the success URL includes
// `?payment=success&session_id=...`. Call finalize-checkout-session so the
// appointment flips from PENDING to PAID, then scrub the query params so
// refreshing doesn't re-trigger it.
onMounted(async () => {
  const payment = route.query.payment
  const sessionId = route.query.session_id
  if (payment === 'success' && typeof sessionId === 'string' && sessionId) {
    if (finalizedSessions.has(sessionId)) {
      router.replace({ name: 'customer-appointments' })
      return
    }
    finalizedSessions.add(sessionId)
    // Strip the query string synchronously first so any re-entry (tab
    // restore, back button) doesn't see the params at all.
    router.replace({ name: 'customer-appointments' })
    try {
      await api.post('/api/bookings/finalize-checkout-session/', { session_id: sessionId })
      toast.success('Payment confirmed')
      queryClient.invalidateQueries({ queryKey: ['appointments'] })
    } catch {
      toast.error('Could not confirm payment. Please check your appointments.')
    }
  } else if (payment === 'cancelled') {
    toast.info('Payment cancelled. Your booking is still held as pending.')
    router.replace({ name: 'customer-appointments' })
  }
})

const tabEndpoints: Record<Tab, string> = {
  upcoming: '/api/bookings/my/upcoming/',
  past: '/api/bookings/my/past/',
}

const { data: appointments, isLoading } = useQuery<AppointmentData[]>({
  queryKey: computed(() => ['appointments', activeTab.value]),
  queryFn: () =>
    api.get<AppointmentData[]>(tabEndpoints[activeTab.value]).then((r) => r.data),
})

const tabs = computed<Array<{ id: Tab; label: string }>>(() => [
  { id: 'upcoming', label: t('appointments.tabs.upcoming') },
  { id: 'past', label: t('appointments.tabs.past') },
])

// ---- Confirmation modal ----
type PendingAction =
  | { type: 'cancel'; appointment: AppointmentData }
  | { type: 'reschedule'; appointment: AppointmentData }
  | null

const pending = ref<PendingAction>(null)
const isConfirming = ref(false)

const modal = computed(() => {
  if (!pending.value) return null
  if (pending.value.type === 'cancel') {
    return {
      title: 'Cancel this appointment?',
      body: 'Your slot will be released immediately. This action cannot be undone.',
      confirmLabel: 'Cancel appointment',
      keepLabel: 'Keep it',
      tone: 'danger' as const,
    }
  }
  return {
    title: 'Reschedule this appointment?',
    body: 'Your current slot will be released and you\'ll pick a new time.',
    confirmLabel: 'Reschedule',
    keepLabel: 'Never mind',
    tone: 'neutral' as const,
  }
})

function requestCancel(id: number) {
  const appt = appointments.value?.find((a) => a.id === id)
  if (appt) pending.value = { type: 'cancel', appointment: appt }
}

function requestReschedule(appointment: AppointmentData) {
  pending.value = { type: 'reschedule', appointment }
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
    queryClient.invalidateQueries({ queryKey: ['appointments'] })
    toast.success('Appointment cancelled')
  },
  onError: () => {
    toast.error('Failed to cancel appointment. Please try again.')
  },
})

async function confirmAction() {
  if (!pending.value) return
  const action = pending.value
  isConfirming.value = true
  try {
    if (action.type === 'cancel') {
      await cancelMutation.mutateAsync(action.appointment.id)
      pending.value = null
      return
    }

    // Reschedule is now a single atomic backend call — don't cancel yet.
    // Just navigate to the booking page to pick a new slot.
    const serviceIds = action.appointment.services
      .map((s) => s.service_id)
      .filter((id): id is number => id !== null)
      .join(',')

    pending.value = null
    router.push({
      path: `/customer/book/${action.appointment.barber}`,
      query: {
        reschedule: String(action.appointment.id),
        ...(serviceIds ? { services: serviceIds } : {}),
      },
    })
  } catch {
    toast.error('Something went wrong. Please try again.')
  } finally {
    isConfirming.value = false
  }
}
</script>

<template>
  <CustomerLayout>
    <!-- Header -->
    <section class="max-w-4xl mx-auto px-5 md:px-8 lg:px-12 pt-6 md:pt-8">
      <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
        {{ t('appointments.title') }}
      </h1>
    </section>

    <!-- Tabs -->
    <div class="sticky top-16 z-20 bg-white border-b border-slate-200 mt-5 md:mt-6">
      <div class="max-w-4xl mx-auto px-5 md:px-8 lg:px-12">
        <nav
          role="tablist"
          aria-label="Appointments sections"
          class="flex items-center gap-1 overflow-x-auto -mb-px"
        >
          <button
            v-for="t in tabs"
            :key="t.id"
            role="tab"
            type="button"
            :aria-selected="activeTab === t.id"
            :class="[
              'inline-flex items-center gap-2 px-4 py-3.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
              activeTab === t.id
                ? 'border-slate-900 text-slate-900'
                : 'border-transparent text-slate-500 hover:text-slate-900',
            ]"
            @click="activeTab = t.id"
          >
            {{ t.label }}
          </button>
        </nav>
      </div>
    </div>

    <!-- Content -->
    <section class="max-w-4xl mx-auto px-5 md:px-8 lg:px-12 py-8 md:py-10">
      <!-- Loading -->
      <div v-if="isLoading" class="space-y-3">
        <SkeletonBlock v-for="n in 3" :key="n" height="8rem" />
      </div>

      <!-- Empty -->
      <EmptyState
        v-else-if="!appointments || appointments.length === 0"
        :title="activeTab === 'upcoming' ? t('appointments.empty.upcoming') : t('appointments.empty.past')"
        :action-to="activeTab === 'upcoming' ? '/customer/explore' : undefined"
        :action-label="activeTab === 'upcoming' ? t('appointments.empty.action') : undefined"
      />

      <!-- List -->
      <div v-else class="space-y-3">
        <AppointmentCard
          v-for="appt in appointments"
          :key="appt.id"
          :appointment="appt"
          variant="customer"
          :loading="pending?.appointment.id === appt.id && isConfirming"
          @cancel="requestCancel"
          @reschedule="requestReschedule"
        />
      </div>
    </section>

    <!-- Confirm modal -->
    <Teleport to="body">
      <Transition name="fade">
        <div
          v-if="pending && modal"
          class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-end md:items-center justify-center md:p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-modal-title"
          @click.self="closeModal"
        >
          <Transition name="slide-up">
            <div
              v-if="pending"
              class="w-full md:max-w-md bg-white rounded-t-2xl md:rounded-2xl shadow-xl p-5 md:p-6"
            >
              <h2 id="confirm-modal-title" class="text-lg font-semibold text-slate-900 tracking-tight">
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
                <p v-if="pending.appointment.barber_name" class="mt-0.5 text-sm text-slate-500">
                  with {{ pending.appointment.barber_name }}
                  <span v-if="pending.appointment.shop_name"> · {{ pending.appointment.shop_name }}</span>
                </p>
              </div>

              <!-- Actions -->
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
                  :class="[
                    'inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed',
                    modal.tone === 'danger'
                      ? 'bg-red-600 hover:bg-red-700 text-white'
                      : 'bg-slate-900 hover:bg-slate-800 text-white',
                  ]"
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
  </CustomerLayout>
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
