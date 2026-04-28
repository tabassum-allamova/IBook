<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import DateScroller from '@/components/booking/DateScroller.vue'
import SlotGrid from '@/components/booking/SlotGrid.vue'
import ServiceSelector from '@/components/booking/ServiceSelector.vue'
import StripePaymentForm from '@/components/booking/StripePaymentForm.vue'
import BookingConfirmation from '@/components/booking/BookingConfirmation.vue'
import type { Service } from '@/components/booking/ServiceSelector.vue'
import type { AppointmentResult } from '@/components/booking/BookingConfirmation.vue'
import api from '@/lib/axios'

const toast = useToast()
const { t } = useI18n()

const props = defineProps<{
  barberId: string
}>()

const route = useRoute()
const router = useRouter()
const queryClient = useQueryClient()

// Reschedule mode — when set, we update an existing appointment instead of creating a new one.
const rescheduleId = computed<number | null>(() => {
  const raw = route.query.reschedule
  if (typeof raw !== 'string' || raw === '' || raw === 'true') return null
  const n = Number(raw)
  return Number.isFinite(n) && n > 0 ? n : null
})
const isReschedule = computed(() => rescheduleId.value !== null)

const barberIdNum = computed(() => Number(props.barberId))

interface BarberMeta {
  id: number
  full_name: string
  avatar: string | null
  shop_name: string | null
}

const { data: barber } = useQuery<BarberMeta>({
  queryKey: computed(() => ['barber-meta', barberIdNum.value]),
  queryFn: async () => {
    const res = await api.get<BarberMeta>(`/api/barbers/${barberIdNum.value}/`)
    return res.data
  },
  enabled: computed(() => !isNaN(barberIdNum.value)),
})

// When STRIPE_SECRET_KEY isn't configured on the backend, hide the "Pay
// Online" option so the user never gets a 503 mid-checkout.
const { data: paymentConfig } = useQuery<{ stripe_enabled: boolean }>({
  queryKey: ['payment-config'],
  queryFn: async () => {
    const res = await api.get<{ stripe_enabled: boolean }>('/api/bookings/payment-config/')
    return res.data
  },
  staleTime: 5 * 60 * 1000,
})
const stripeEnabled = computed(() => paymentConfig.value?.stripe_enabled ?? false)

// Format a Date as YYYY-MM-DD in local time so the initial selection matches
// what the DateScroller emits (UTC-based ISO can be off by one day in
// non-UTC timezones).
function toLocalIso(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

const step = ref(1)
const selectedServices = ref<Service[]>([])
const selectedDate = ref(toLocalIso(new Date()))
const selectedSlot = ref('')
const paymentMethod = ref<'ONLINE' | 'AT_SHOP'>('AT_SHOP')

// Default to ONLINE only once we know Stripe is configured. Otherwise stay
// on AT_SHOP and hide the ONLINE radio in the template.
watch(stripeEnabled, (enabled) => {
  if (enabled && step.value < 3) paymentMethod.value = 'ONLINE'
}, { immediate: true })
const bookingResult = ref<AppointmentResult | null>(null)
const paymentError = ref('')
const isStartingCheckout = ref(false)

const selectedServiceIds = computed(() => selectedServices.value.map((s) => s.id))

const totalPrice = computed(() =>
  selectedServices.value.reduce((sum, s) => sum + s.price, 0),
)

const totalDuration = computed(() =>
  selectedServices.value.reduce((sum, s) => sum + s.duration_minutes, 0),
)

function formatPrice(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

const serviceSelectorRef = ref<InstanceType<typeof ServiceSelector> | null>(null)

onMounted(() => {
  const servicesParam = route.query.services as string | undefined
  const isResched = route.query.reschedule !== undefined
  if (!(isResched && servicesParam)) return

  const ids = servicesParam.split(',').map(Number).filter(Boolean)
  if (ids.length === 0) return

  // 1) Preselect the services as soon as ServiceSelector mounts.
  const unwatchSelector = watch(
    () => serviceSelectorRef.value,
    (selector) => {
      if (!selector) return
      selector.preselectServices(ids)
      nextTick(() => unwatchSelector())
    },
    { immediate: true },
  )

  // 2) Only advance to step 2 once the selector has actually resolved the
  //    services list and emitted them back — otherwise selectedServices is [],
  //    which disables the slots query and shows "No open slots".
  const unwatchServices = watch(
    () => selectedServices.value.length,
    (n) => {
      if (n >= ids.length) {
        step.value = 2
        nextTick(() => unwatchServices())
      }
    },
  )
})

const { data: slotsData, isLoading: slotsLoading } = useQuery<{
  slots: string[]
}>({
  queryKey: computed(() => [
    'slots',
    barberIdNum.value,
    selectedDate.value,
    selectedServiceIds.value.join(','),
    rescheduleId.value,
  ]),
  queryFn: () => {
    const params: Record<string, string | number> = {
      barber_id: barberIdNum.value,
      date: selectedDate.value,
      service_ids: selectedServiceIds.value.join(','),
    }
    if (rescheduleId.value !== null) params.exclude_appointment_id = rescheduleId.value
    return api.get('/api/bookings/slots/', { params }).then((r) => r.data)
  },
  enabled: computed(
    () => !!selectedDate.value && selectedServiceIds.value.length > 0,
  ),
})

const availableSlots = computed(() => slotsData.value?.slots ?? [])

watch(
  () => selectedDate.value,
  () => {
    selectedSlot.value = ''
  },
)

const rescheduleMutation = useMutation({
  mutationFn: (payload: { date: string; start_time: string; service_ids: number[] }) =>
    api.post(`/api/bookings/${rescheduleId.value}/reschedule/`, payload).then((r) => r.data),
  onSuccess: (data: AppointmentResult) => {
    bookingResult.value = data
    queryClient.invalidateQueries({ queryKey: ['appointments'] })
    queryClient.invalidateQueries({ queryKey: ['slots'] })
    step.value = 4
    toast.success('Appointment rescheduled')
  },
  onError: (error: unknown) => {
    const err = error as { response?: { status?: number; data?: { detail?: string } } }
    if (err.response?.status === 409) {
      toast.error('This slot was just booked by someone else. Please pick another time.')
      selectedSlot.value = ''
      queryClient.invalidateQueries({ queryKey: ['slots'] })
    } else {
      toast.error(err.response?.data?.detail ?? 'Failed to reschedule. Please try again.')
    }
  },
})

function confirmReschedule() {
  if (!selectedSlot.value || selectedServiceIds.value.length === 0 || rescheduleId.value === null) return
  rescheduleMutation.mutate({
    date: selectedDate.value,
    start_time: selectedSlot.value,
    service_ids: selectedServiceIds.value,
  })
}

const bookMutation = useMutation({
  mutationFn: (payload: {
    barber_id: number
    date: string
    start_time: string
    service_ids: number[]
    payment_method: 'ONLINE' | 'AT_SHOP'
  }) => api.post('/api/bookings/', payload).then((r) => r.data),
  onSuccess: async (data: AppointmentResult) => {
    bookingResult.value = data
    queryClient.invalidateQueries({ queryKey: ['slots'] })
    queryClient.invalidateQueries({ queryKey: ['appointments'] })

    // ONLINE → create Stripe session tied to this appointment, then redirect.
    // If the user abandons Stripe, the appointment stays PENDING and can be
    // resumed / cancelled from the appointments page.
    if (data.payment_method === 'ONLINE') {
      isStartingCheckout.value = true
      try {
        const res = await api.post<{ url: string }>(
          '/api/bookings/create-checkout-session/',
          {
            amount: data.total_price,
            description: 'IBook barbershop appointment',
            appointment_id: data.id,
          },
        )
        if (res.data.url) {
          window.location.href = res.data.url
          return
        }
        toast.error('Could not start checkout. Please try again.')
      } catch (err) {
        const e = err as { response?: { data?: { detail?: string } } }
        toast.error(e.response?.data?.detail ?? 'Could not start checkout. Please try again.')
      } finally {
        isStartingCheckout.value = false
      }
      return
    }

    step.value = 4
    toast.success('Appointment booked!')
  },
  onError: (error: unknown) => {
    const err = error as { response?: { status?: number; data?: { detail?: string } } }
    if (err.response?.status === 409) {
      toast.error('This slot was just booked by someone else. Please pick another time.')
      selectedSlot.value = ''
      step.value = 2
      queryClient.invalidateQueries({ queryKey: ['slots'] })
    } else if (err.response?.status === 400) {
      const msg = err.response.data?.detail ?? 'Payment declined. Please try again.'
      paymentError.value = msg
      toast.error(msg)
    } else {
      paymentError.value = 'Something went wrong. Please try again.'
      toast.error('Something went wrong. Please try again.')
    }
  },
})

function handlePayment(data: { payment_method: 'ONLINE' | 'AT_SHOP' }) {
  // Guard against a second click while the first /api/bookings/ call is in
  // flight (slow network, double-click, keyboard Enter repeat). The button
  // is disabled via `loading`, but the handler itself still gets called if
  // the disabled state is bypassed — belt + braces.
  if (bookMutation.isPending.value || isStartingCheckout.value) return
  paymentError.value = ''
  bookMutation.mutate({
    barber_id: barberIdNum.value,
    date: selectedDate.value,
    start_time: selectedSlot.value,
    service_ids: selectedServiceIds.value,
    payment_method: data.payment_method,
  })
}

function handleServicesUpdate(services: Service[]) {
  selectedServices.value = services
}

function formatDateLabel(iso: string): string {
  if (!iso) return ''
  const d = new Date(iso + 'T00:00:00')
  if (isNaN(d.getTime())) return iso
  return d.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  })
}
</script>

<template>
  <CustomerLayout>
    <!-- Back link -->
    <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-5">
      <RouterLink
        :to="{ name: 'customer-barber-profile', params: { barberId: barberIdNum } }"
        class="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-slate-900 transition-colors"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to profile
      </RouterLink>
    </div>

    <!-- Confirmation takes over the page -->
    <template v-if="step === 4 && bookingResult">
      <section class="max-w-3xl mx-auto px-5 md:px-8 lg:px-12 pt-8 md:pt-12 pb-16">
        <BookingConfirmation
          :appointment="bookingResult"
          :barber-id="props.barberId"
        />
      </section>
    </template>

    <!-- Booking flow -->
    <template v-else>
      <!-- Header -->
      <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-6 md:pt-8 pb-6 md:pb-8">
        <div class="flex items-center gap-4">
          <!-- Barber avatar -->
          <div
            class="flex-shrink-0 h-14 w-14 md:h-16 md:w-16 rounded-full overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center"
          >
            <img
              v-if="barber?.avatar"
              :src="barber.avatar"
              :alt="barber.full_name"
              class="w-full h-full object-cover"
            />
            <svg
              v-else
              class="h-7 w-7 text-slate-300"
              fill="none"
              stroke="currentColor"
              stroke-width="1.4"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>

          <!-- Title + barber -->
          <div class="min-w-0">
            <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight truncate">
              <template v-if="barber">{{ barber.full_name }}</template>
              <template v-else>…</template>
            </h1>
            <p v-if="barber?.shop_name" class="mt-1 text-sm text-slate-500 truncate">
              {{ barber.shop_name }}
            </p>
          </div>
        </div>

      </section>

      <!-- Grid: step content + summary -->
      <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pb-16 md:pb-20">
        <div class="grid lg:grid-cols-12 gap-8 lg:gap-10 items-start">
          <!-- Step content -->
          <div class="lg:col-span-8 min-w-0">
            <!-- Step 1: Services -->
            <div v-if="step === 1">
              <h2 class="text-lg font-semibold text-slate-900 tracking-tight mb-1">
                {{ t('booking.services.title') }}
              </h2>
              <p class="text-sm text-slate-500 mb-6">
                {{ t('booking.services.subtitle') }}
              </p>
              <ServiceSelector
                ref="serviceSelectorRef"
                :barber-id="barberIdNum"
                @update="handleServicesUpdate"
              />

              <div class="mt-8">
                <button
                  type="button"
                  class="w-full inline-flex items-center justify-center gap-2 h-11 px-6 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="selectedServices.length === 0"
                  @click="step = 2"
                >
                  {{ t('booking.services.continue') }}
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Step 2: Date & time -->
            <div v-else-if="step === 2">
              <h2 class="text-lg font-semibold text-slate-900 tracking-tight mb-1">
                {{ t('booking.slot.title') }}
              </h2>
              <p class="text-sm text-slate-500 mb-6">
                {{ isReschedule ? t('booking.slot.rescheduleSubtitle') : t('booking.slot.subtitle') }}
              </p>

              <DateScroller :selected="selectedDate" @select="(d) => (selectedDate = d)" />

              <div class="mt-7">
                <SlotGrid
                  :slots="availableSlots"
                  :selected="selectedSlot"
                  :loading="slotsLoading"
                  @select="(s) => (selectedSlot = s)"
                />
              </div>

              <div class="mt-8 flex flex-col-reverse sm:flex-row gap-3">
                <button
                  type="button"
                  class="flex-1 inline-flex items-center justify-center gap-1.5 h-11 px-6 rounded-lg border border-slate-200 bg-white text-slate-700 font-semibold hover:border-slate-400 hover:text-slate-900 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="rescheduleMutation.isPending.value"
                  @click="step = 1"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                  </svg>
                  {{ t('booking.slot.back') }}
                </button>
                <button
                  v-if="isReschedule"
                  type="button"
                  class="flex-1 inline-flex items-center justify-center gap-2 h-11 px-6 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="!selectedSlot || rescheduleMutation.isPending.value"
                  @click="confirmReschedule"
                >
                  <svg
                    v-if="rescheduleMutation.isPending.value"
                    class="h-4 w-4 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                    <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                  </svg>
                  {{ rescheduleMutation.isPending.value ? t('booking.slot.rescheduling') : t('booking.slot.confirmReschedule') }}
                </button>
                <button
                  v-else
                  type="button"
                  class="flex-1 inline-flex items-center justify-center gap-2 h-11 px-6 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="!selectedSlot"
                  @click="step = 3"
                >
                  {{ t('booking.slot.continue') }}
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>

            <!-- Step 3: Payment -->
            <div v-else-if="step === 3">
              <h2 class="text-lg font-semibold text-slate-900 tracking-tight mb-1">
                {{ t('booking.payment.heading') }}
              </h2>
              <p class="text-sm text-slate-500 mb-6">
                {{ paymentMethod === 'ONLINE' ? t('booking.payment.holdOnline') : t('booking.payment.holdAtShop') }}
              </p>

              <!-- Payment method -->
              <div :class="stripeEnabled ? 'grid sm:grid-cols-2 gap-3 mb-6' : 'grid grid-cols-1 gap-3 mb-6'">
                <label
                  v-if="stripeEnabled"
                  class="relative flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-colors bg-white"
                  :class="
                    paymentMethod === 'ONLINE'
                      ? 'border-slate-900 ring-2 ring-slate-900/10'
                      : 'border-slate-200 hover:border-slate-400'
                  "
                >
                  <input
                    v-model="paymentMethod"
                    type="radio"
                    value="ONLINE"
                    class="mt-1 h-4 w-4 accent-slate-900 flex-shrink-0"
                  />
                  <div class="min-w-0">
                    <p class="text-base font-semibold text-slate-900 leading-tight">{{ t('booking.payment.online') }}</p>
                    <p class="text-sm text-slate-500 mt-1">{{ t('booking.payment.onlineDesc') }}</p>
                  </div>
                </label>

                <label
                  class="relative flex items-start gap-3 p-4 rounded-xl border cursor-pointer transition-colors bg-white"
                  :class="
                    paymentMethod === 'AT_SHOP'
                      ? 'border-slate-900 ring-2 ring-slate-900/10'
                      : 'border-slate-200 hover:border-slate-400'
                  "
                >
                  <input
                    v-model="paymentMethod"
                    type="radio"
                    value="AT_SHOP"
                    class="mt-1 h-4 w-4 accent-slate-900 flex-shrink-0"
                  />
                  <div class="min-w-0">
                    <p class="text-base font-semibold text-slate-900 leading-tight">{{ t('booking.payment.atShop') }}</p>
                    <p class="text-sm text-slate-500 mt-1">{{ t('booking.payment.atShopDesc') }}</p>
                  </div>
                </label>
              </div>

              <!-- Error -->
              <div
                v-if="paymentError"
                class="mb-5 px-4 py-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm"
              >
                {{ paymentError }}
              </div>

              <StripePaymentForm
                :key="paymentMethod"
                :total-price="totalPrice"
                :payment-method="paymentMethod"
                :loading="bookMutation.isPending.value || isStartingCheckout"
                @confirm="handlePayment"
              />

              <div class="mt-5">
                <button
                  type="button"
                  class="inline-flex items-center gap-1.5 h-11 px-5 rounded-lg border border-slate-200 bg-white text-slate-700 font-semibold hover:border-slate-400 hover:text-slate-900 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                  :disabled="bookMutation.isPending.value"
                  @click="step = 2"
                >
                  <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
                  </svg>
                  {{ t('booking.payment.backToTime') }}
                </button>
              </div>
            </div>
          </div>

          <!-- Sidebar summary -->
          <aside class="lg:col-span-4">
            <div class="lg:sticky lg:top-20 rounded-xl border border-slate-200 bg-white p-5 md:p-6">
              <h3 class="text-base font-semibold text-slate-900 tracking-tight mb-1">
                {{ t('booking.summary.title') }}
              </h3>
              <p class="text-sm text-slate-500 mb-5">
                {{ t('booking.summary.subtitle') }}
              </p>

              <!-- Barber -->
              <div v-if="barber" class="flex items-center gap-3 pb-4 mb-4 border-b border-slate-100">
                <div class="flex-shrink-0 h-10 w-10 rounded-full overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center">
                  <img
                    v-if="barber.avatar"
                    :src="barber.avatar"
                    :alt="barber.full_name"
                    class="w-full h-full object-cover"
                  />
                  <svg
                    v-else
                    class="h-5 w-5 text-slate-300"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.4"
                    viewBox="0 0 24 24"
                  >
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <div class="min-w-0">
                  <p class="text-sm font-semibold text-slate-900 truncate">{{ barber.full_name }}</p>
                  <p v-if="barber.shop_name" class="text-sm text-slate-500 truncate">
                    {{ barber.shop_name }}
                  </p>
                </div>
              </div>

              <!-- Services -->
              <div v-if="selectedServices.length > 0" class="space-y-3 pb-4 border-b border-slate-100">
                <div
                  v-for="s in selectedServices"
                  :key="s.id"
                  class="flex items-baseline justify-between gap-3"
                >
                  <div class="min-w-0">
                    <p class="text-sm text-slate-900 truncate">{{ s.name }}</p>
                    <p class="text-sm text-slate-500 mt-0.5">{{ s.duration_minutes }} {{ t('booking.summary.minutes') }}</p>
                  </div>
                  <p class="text-sm font-medium text-slate-900 whitespace-nowrap tabular-nums">
                    {{ formatPrice(s.price) }}
                  </p>
                </div>
              </div>
              <p v-else class="text-sm text-slate-400 pb-4 border-b border-slate-100">
                {{ t('booking.summary.servicesPlaceholder') }}
              </p>

              <!-- Date / time / duration -->
              <dl class="py-4 border-b border-slate-100 space-y-2 text-sm">
                <div class="flex items-baseline justify-between gap-3">
                  <dt class="text-sm font-medium text-slate-500">{{ t('booking.summary.date') }}</dt>
                  <dd class="text-slate-900">
                    <span v-if="selectedDate">{{ formatDateLabel(selectedDate) }}</span>
                    <span v-else class="text-slate-400">—</span>
                  </dd>
                </div>
                <div class="flex items-baseline justify-between gap-3">
                  <dt class="text-sm font-medium text-slate-500">{{ t('booking.summary.time') }}</dt>
                  <dd class="text-slate-900 tabular-nums">
                    <span v-if="selectedSlot">{{ selectedSlot }}</span>
                    <span v-else class="text-slate-400">—</span>
                  </dd>
                </div>
                <div class="flex items-baseline justify-between gap-3">
                  <dt class="text-sm font-medium text-slate-500">{{ t('booking.summary.duration') }}</dt>
                  <dd class="text-slate-900 tabular-nums">
                    <span v-if="totalDuration > 0">{{ totalDuration }} {{ t('booking.summary.minutes') }}</span>
                    <span v-else class="text-slate-400">—</span>
                  </dd>
                </div>
              </dl>

              <!-- Total -->
              <div class="pt-4 flex items-baseline justify-between gap-3">
                <span class="text-sm font-medium text-slate-500">{{ t('booking.summary.total') }}</span>
                <span class="text-xl font-bold text-slate-900 tabular-nums">
                  {{ totalPrice > 0 ? formatPrice(totalPrice) : '—' }}
                </span>
              </div>
            </div>
          </aside>
        </div>
      </section>
    </template>
  </CustomerLayout>
</template>
