<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import api from '@/lib/axios'
import type { AppointmentData } from '@/components/booking/AppointmentCard.vue'

const props = defineProps<{
  appointmentId: string
}>()

const router = useRouter()
const queryClient = useQueryClient()

// Fetch past appointments and find the matching one
const { data: pastAppointments, isLoading: isLoadingAppt } = useQuery<AppointmentData[]>({
  queryKey: computed(() => ['appointment-for-review', props.appointmentId]),
  queryFn: async () => {
    const res = await api.get<AppointmentData[]>('/api/bookings/my/past/')
    return res.data
  },
  staleTime: 0,
})

const appointment = computed(() =>
  pastAppointments.value?.find((a) => a.id === Number(props.appointmentId)) ?? null,
)

// Star rating state
const overallRating = ref(0)
const hoverOverall = ref(0)
const reviewText = ref('')

interface ServiceRating {
  service_name: string
  rating: number
  hover: number
}
const serviceRatings = ref<ServiceRating[]>([])

// Populate service ratings when appointment loads
watch(appointment, (appt) => {
  if (appt && serviceRatings.value.length === 0) {
    serviceRatings.value = appt.services.map((s) => ({
      service_name: s.service_name,
      rating: 0,
      hover: 0,
    }))
  }
})

// Success state
const submitted = ref(false)

// Mutation
const { mutate: submitReview, isPending, error: mutationError } = useMutation({
  mutationFn: () =>
    api.post('/api/reviews/', {
      appointment_id: Number(props.appointmentId),
      rating: overallRating.value,
      text: reviewText.value,
      service_ratings: serviceRatings.value
        .filter((s) => s.rating > 0)
        .map((s) => ({ service_name: s.service_name, rating: s.rating })),
    }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['appointments'] })
    submitted.value = true
    setTimeout(() => {
      router.push('/customer/appointments')
    }, 1500)
  },
})

const errorMessage = computed(() => {
  if (!mutationError.value) return null
  const err = mutationError.value as { response?: { data?: { detail?: string } } }
  return err?.response?.data?.detail ?? 'Something went wrong. Please try again.'
})

function formatDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  })
}
</script>

<template>
  <CustomerLayout>
    <div class="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-20">

      <!-- Back link -->
      <RouterLink
        to="/customer/appointments"
        class="inline-flex items-center gap-1.5 text-sm text-ibook-brown-500 hover:text-ibook-brown-800 transition-colors mb-6"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Appointments
      </RouterLink>

      <!-- Page title -->
      <h1 class="text-2xl font-bold text-ibook-brown-900 mb-8">Leave a Review</h1>

      <!-- Loading skeleton -->
      <div v-if="isLoadingAppt" class="space-y-5">
        <div class="h-24 bg-ibook-brown-100 rounded-2xl animate-pulse" />
        <div class="h-40 bg-ibook-brown-100 rounded-2xl animate-pulse" />
        <div class="h-32 bg-ibook-brown-100 rounded-2xl animate-pulse" />
      </div>

      <!-- Not found state -->
      <div
        v-else-if="!appointment"
        class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-12 text-center"
      >
        <p class="text-ibook-brown-700 font-semibold">Appointment not found.</p>
        <p class="text-ibook-brown-400 text-sm mt-1">This appointment may not be eligible for a review.</p>
        <RouterLink
          to="/customer/appointments"
          class="mt-4 inline-block py-2 px-4 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          Back to Appointments
        </RouterLink>
      </div>

      <!-- Success state -->
      <div
        v-else-if="submitted"
        class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-12 flex flex-col items-center text-center animate-fade-in"
      >
        <div class="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-4">
          <svg class="h-8 w-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 class="text-xl font-bold text-ibook-brown-900 mb-2">Thank you!</h2>
        <p class="text-ibook-brown-500 text-sm">Your review has been submitted. Redirecting...</p>
      </div>

      <!-- Review form -->
      <div v-else class="space-y-6">

        <!-- Appointment summary card -->
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-xs font-semibold uppercase tracking-wide text-ibook-brown-400 mb-3">Appointment Details</p>
          <div class="space-y-1.5">
            <p class="text-sm font-semibold text-ibook-brown-900">{{ appointment.barber_name }}</p>
            <p class="text-sm text-ibook-brown-500">{{ formatDate(appointment.date) }} at {{ appointment.start_time }}</p>
            <p class="text-xs text-ibook-brown-400">
              {{ appointment.services.map((s) => s.service_name).join(', ') }}
            </p>
          </div>
        </div>

        <!-- Overall rating -->
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-semibold text-ibook-brown-900 mb-4">How was your overall experience?</p>
          <div class="flex items-center gap-1">
            <button
              v-for="star in 5"
              :key="star"
              type="button"
              class="h-9 w-9 flex items-center justify-center transition-colors duration-150 cursor-pointer rounded-md hover:scale-110 active:scale-95"
              @mouseenter="hoverOverall = star"
              @mouseleave="hoverOverall = 0"
              @click="overallRating = star"
            >
              <svg
                class="h-7 w-7 transition-colors duration-150"
                :class="star <= (hoverOverall || overallRating) ? 'text-ibook-gold-400 fill-current' : 'text-ibook-brown-200 fill-current'"
                viewBox="0 0 20 20"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </button>
            <span v-if="overallRating > 0" class="ml-2 text-sm text-ibook-brown-500">
              {{ ['', 'Poor', 'Fair', 'Good', 'Very Good', 'Excellent'][overallRating] }}
            </span>
          </div>
        </div>

        <!-- Per-service ratings -->
        <div
          v-if="serviceRatings.length > 0"
          class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5"
        >
          <p class="text-sm font-semibold text-ibook-brown-900 mb-4">Rate individual services <span class="font-normal text-ibook-brown-400">(optional)</span></p>
          <div class="space-y-4">
            <div v-for="(svc, idx) in serviceRatings" :key="idx">
              <p class="text-xs font-medium text-ibook-brown-700 mb-2">{{ svc.service_name }}</p>
              <div class="flex items-center gap-1">
                <button
                  v-for="star in 5"
                  :key="star"
                  type="button"
                  class="h-8 w-8 flex items-center justify-center transition-colors duration-150 cursor-pointer rounded-md"
                  @mouseenter="svc.hover = star"
                  @mouseleave="svc.hover = 0"
                  @click="svc.rating = star"
                >
                  <svg
                    class="h-5 w-5 transition-colors duration-150"
                    :class="star <= (svc.hover || svc.rating) ? 'text-ibook-gold-400 fill-current' : 'text-ibook-brown-200 fill-current'"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Written review -->
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <label for="review-text" class="block text-sm font-semibold text-ibook-brown-900 mb-3">
            Write a review <span class="font-normal text-ibook-brown-400">(optional)</span>
          </label>
          <textarea
            id="review-text"
            v-model="reviewText"
            rows="4"
            placeholder="Share your experience..."
            class="w-full rounded-lg border border-ibook-brown-200 text-ibook-brown-900 text-sm placeholder-ibook-brown-300 resize-none py-3 px-3.5 focus:outline-none focus:ring-2 focus:ring-ibook-brown-400 focus:border-transparent transition-shadow"
          />
        </div>

        <!-- Error message -->
        <p v-if="errorMessage" class="text-sm text-red-600 font-medium">
          {{ errorMessage }}
        </p>

        <!-- Submit -->
        <button
          type="button"
          class="w-full py-3 px-6 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white font-semibold rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer text-base"
          :disabled="overallRating === 0 || isPending"
          @click="submitReview()"
        >
          <span v-if="isPending" class="inline-flex items-center gap-2">
            <span class="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Submitting...
          </span>
          <span v-else>Submit Review</span>
        </button>

        <p v-if="overallRating === 0" class="text-xs text-ibook-brown-400 text-center -mt-2">
          Please select an overall star rating to continue.
        </p>

      </div>
    </div>
  </CustomerLayout>
</template>
