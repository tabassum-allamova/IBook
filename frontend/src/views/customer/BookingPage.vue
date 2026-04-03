<script setup lang="ts">
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
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

const props = defineProps<{
  barberId: string
}>()

const route = useRoute()
const queryClient = useQueryClient()

const barberIdNum = computed(() => Number(props.barberId))

// Wizard state
const step = ref(1)
const selectedServices = ref<Service[]>([])
const selectedDate = ref(new Date().toISOString().split('T')[0])
const selectedSlot = ref('')
const paymentMethod = ref<'ONLINE' | 'AT_SHOP'>('ONLINE')
const pendingCheckoutUrl = ref('')
const bookingResult = ref<AppointmentResult | null>(null)
const paymentError = ref('')

// Computed helpers
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

// Ref to ServiceSelector for reschedule pre-population
const serviceSelectorRef = ref<InstanceType<typeof ServiceSelector> | null>(null)

// Reschedule pre-population
onMounted(() => {
  const reschedule = route.query.reschedule === 'true'
  const servicesParam = route.query.services as string | undefined
  if (reschedule && servicesParam) {
    const ids = servicesParam.split(',').map(Number).filter(Boolean)
    if (ids.length > 0) {
      // Wait for ServiceSelector to load, then pre-select
      let unwatched = false
      const unwatch = watch(
        () => serviceSelectorRef.value,
        (selector) => {
          if (selector && !unwatched) {
            selector.preselectServices(ids)
            step.value = 2
            unwatched = true
            nextTick(() => unwatch())
          }
        },
        { immediate: true },
      )
    }
  }
})

// Slot fetching
const { data: slotsData, isLoading: slotsLoading } = useQuery<{
  slots: string[]
}>({
  queryKey: computed(() => [
    'slots',
    barberIdNum.value,
    selectedDate.value,
    selectedServiceIds.value.join(','),
  ]),
  queryFn: () =>
    api
      .get('/api/bookings/slots/', {
        params: {
          barber_id: barberIdNum.value,
          date: selectedDate.value,
          service_ids: selectedServiceIds.value.join(','),
        },
      })
      .then((r) => r.data),
  enabled: computed(
    () => !!selectedDate.value && selectedServiceIds.value.length > 0,
  ),
})

const availableSlots = computed(() => slotsData.value?.slots ?? [])

// Clear slot when date changes
watch(
  () => selectedDate.value,
  () => {
    selectedSlot.value = ''
  },
)

// Booking mutation
const bookMutation = useMutation({
  mutationFn: (payload: {
    barber_id: number
    date: string
    start_time: string
    service_ids: number[]
    payment_method: 'ONLINE' | 'AT_SHOP'
  }) => api.post('/api/bookings/', payload).then((r) => r.data),
  onSuccess: (data: AppointmentResult) => {
    bookingResult.value = data
    queryClient.invalidateQueries({ queryKey: ['slots'] })
    queryClient.invalidateQueries({ queryKey: ['appointments'] })

    // Online payment: redirect to Stripe checkout instead of showing step 4
    if (pendingCheckoutUrl.value) {
      window.location.href = pendingCheckoutUrl.value
      return
    }

    step.value = 4
    toast.success('Appointment booked!')
  },
  onError: (error: unknown) => {
    const err = error as { response?: { status?: number; data?: { detail?: string } } }
    if (err.response?.status === 409) {
      // Slot taken - go back to step 2 and refetch
      toast.error('This slot was just booked by someone else. Please pick another time.')
      selectedSlot.value = ''
      step.value = 2
      queryClient.invalidateQueries({ queryKey: ['slots'] })
    } else if (err.response?.status === 400) {
      // Payment declined or validation error
      const msg = err.response.data?.detail ?? 'Payment declined. Please try again.'
      paymentError.value = msg
      toast.error(msg)
    } else {
      paymentError.value = 'Something went wrong. Please try again.'
      toast.error('Something went wrong. Please try again.')
    }
  },
})

function handlePayment(data: { payment_method: 'ONLINE' | 'AT_SHOP'; checkoutUrl?: string }) {
  paymentError.value = ''
  pendingCheckoutUrl.value = data.checkoutUrl ?? ''
  bookMutation.mutate({
    barber_id: barberIdNum.value,
    date: selectedDate.value,
    start_time: selectedSlot.value,
    service_ids: selectedServiceIds.value,
    payment_method: data.payment_method,
  })
}

function handlePaymentError(message: string) {
  paymentError.value = message
}

function handleServicesUpdate(services: Service[]) {
  selectedServices.value = services
}
</script>

<template>
  <CustomerLayout>
    <div class="max-w-2xl mx-auto px-4 md:px-8 py-6 md:py-8">
      <!-- Page header -->
      <h1 class="text-xl md:text-2xl font-bold text-ibook-brown-800 mb-6">
        Book an Appointment
      </h1>

      <!-- Step indicator -->
      <div v-if="step < 4" class="flex items-center gap-2 mb-8">
        <template v-for="s in 3" :key="s">
          <div
            class="h-1.5 flex-1 rounded-full transition-colors"
            :class="s <= step ? 'bg-ibook-gold-400' : 'bg-ibook-brown-200'"
          />
        </template>
      </div>

      <!-- Step 1: Service Selection -->
      <div v-if="step === 1">
        <h2 class="text-lg font-semibold text-ibook-brown-800 mb-4">
          Select Services
        </h2>
        <ServiceSelector
          ref="serviceSelectorRef"
          :barber-id="barberIdNum"
          @update="handleServicesUpdate"
        />
        <div class="mt-6">
          <button
            type="button"
            class="w-full py-3 rounded-xl bg-ibook-brown-800 text-white font-semibold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            :class="selectedServices.length > 0 ? 'hover:bg-ibook-brown-700' : ''"
            :disabled="selectedServices.length === 0"
            @click="step = 2"
          >
            Next
          </button>
        </div>
      </div>

      <!-- Step 2: Date & Slot -->
      <div v-else-if="step === 2">
        <h2 class="text-lg font-semibold text-ibook-brown-800 mb-4">
          Pick a Date & Time
        </h2>

        <!-- Summary line -->
        <div class="mb-4 text-sm text-ibook-brown-500">
          {{ selectedServices.length }} service{{ selectedServices.length > 1 ? 's' : '' }}
          &middot; {{ totalDuration }} min &middot; {{ formatPrice(totalPrice) }}
        </div>

        <DateScroller :selected="selectedDate" @select="(d) => (selectedDate = d)" />

        <div class="mt-6">
          <SlotGrid
            :slots="availableSlots"
            :selected="selectedSlot"
            :loading="slotsLoading"
            @select="(s) => (selectedSlot = s)"
          />
        </div>

        <div class="mt-6 flex gap-3">
          <button
            type="button"
            class="flex-1 py-3 rounded-xl border border-ibook-brown-800 text-ibook-brown-800 font-semibold hover:bg-ibook-brown-50 transition-colors cursor-pointer"
            @click="step = 1"
          >
            Back
          </button>
          <button
            type="button"
            class="flex-1 py-3 rounded-xl bg-ibook-brown-800 text-white font-semibold transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            :class="selectedSlot ? 'hover:bg-ibook-brown-700' : ''"
            :disabled="!selectedSlot"
            @click="step = 3"
          >
            Next
          </button>
        </div>
      </div>

      <!-- Step 3: Payment -->
      <div v-else-if="step === 3">
        <h2 class="text-lg font-semibold text-ibook-brown-800 mb-4">
          Payment
        </h2>

        <!-- Summary -->
        <div class="mb-4 text-sm text-ibook-brown-500">
          {{ selectedDate }} at {{ selectedSlot }} &middot;
          {{ selectedServices.length }} service{{ selectedServices.length > 1 ? 's' : '' }}
        </div>

        <!-- Payment method selector -->
        <div class="space-y-3 mb-6">
          <label
            class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors"
            :class="
              paymentMethod === 'ONLINE'
                ? 'border-ibook-gold-400 bg-ibook-brown-50'
                : 'border-ibook-brown-200 bg-white'
            "
          >
            <input
              v-model="paymentMethod"
              type="radio"
              value="ONLINE"
              class="w-4 h-4 accent-ibook-gold-500"
            />
            <span class="font-medium text-ibook-brown-800">Pay Online</span>
          </label>

          <label
            class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors"
            :class="
              paymentMethod === 'AT_SHOP'
                ? 'border-ibook-gold-400 bg-ibook-brown-50'
                : 'border-ibook-brown-200 bg-white'
            "
          >
            <input
              v-model="paymentMethod"
              type="radio"
              value="AT_SHOP"
              class="w-4 h-4 accent-ibook-gold-500"
            />
            <span class="font-medium text-ibook-brown-800">Pay at Shop</span>
          </label>
        </div>

        <!-- Booking error (from mutation) -->
        <div
          v-if="paymentError"
          class="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm"
        >
          {{ paymentError }}
        </div>

        <StripePaymentForm
          :key="paymentMethod"
          :total-price="totalPrice"
          :payment-method="paymentMethod"
          @confirm="handlePayment"
          @error="handlePaymentError"
        />

        <div class="mt-4">
          <button
            type="button"
            class="w-full py-3 rounded-xl border border-ibook-brown-800 text-ibook-brown-800 font-semibold hover:bg-ibook-brown-50 transition-colors cursor-pointer"
            :disabled="bookMutation.isPending.value"
            @click="step = 2"
          >
            Back
          </button>
        </div>
      </div>

      <!-- Step 4: Confirmation -->
      <div v-else-if="step === 4 && bookingResult">
        <BookingConfirmation
          :appointment="bookingResult"
          :barber-id="props.barberId"
        />
      </div>
    </div>
  </CustomerLayout>
</template>
