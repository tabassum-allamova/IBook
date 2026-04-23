<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import api from '@/lib/axios'
import type { AppointmentData } from '@/components/booking/AppointmentCard.vue'

const toast = useToast()
const { t } = useI18n()

const props = defineProps<{
  appointmentId: string
}>()

const router = useRouter()
const queryClient = useQueryClient()

const { data: appointment, isLoading: isLoadingAppt } =
  useQuery<AppointmentData>({
    queryKey: computed(() => ['appointment-for-review', props.appointmentId]),
    queryFn: async () => {
      // Fetch just this one appointment — pulling the full past list was
      // wasteful and broke as soon as the past endpoint paginated.
      const res = await api.get<AppointmentData>(`/api/bookings/${props.appointmentId}/`)
      return res.data
    },
    retry: false,
    staleTime: 0,
  })

const overallRating = ref(0)
const hoverOverall = ref(0)
const reviewText = ref('')

interface ServiceRating {
  service_name: string
  rating: number
  hover: number
}
const serviceRatings = ref<ServiceRating[]>([])

watch(appointment, (appt) => {
  if (appt && serviceRatings.value.length === 0) {
    serviceRatings.value = appt.services.map((s) => ({
      service_name: s.service_name,
      rating: 0,
      hover: 0,
    }))
  }
})

const submitted = ref(false)

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
    toast.success('Review submitted')
    setTimeout(() => router.push('/customer/appointments'), 1400)
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

const ratingLabels = ['', 'Poor', 'Fair', 'Good', 'Very good', 'Excellent']
</script>

<template>
  <CustomerLayout>
    <section class="max-w-3xl mx-auto px-5 md:px-8 lg:px-12 pt-6 md:pt-8 pb-16">
      <!-- Back -->
      <RouterLink
        to="/customer/appointments"
        class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors mb-6"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        {{ t('review.viewAppointments') }}
      </RouterLink>

      <!-- Header -->
      <div class="mb-6 md:mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
          {{ t('review.title') }}
        </h1>
        <p class="mt-1 text-sm text-slate-600">
          {{ appointment ? t('review.subtitle', { barber: appointment.barber_name }) : '' }}
        </p>
      </div>

      <!-- Loading -->
      <div v-if="isLoadingAppt" class="space-y-4">
        <div class="h-24 bg-slate-100 rounded-xl animate-pulse" />
        <div class="h-40 bg-slate-100 rounded-xl animate-pulse" />
        <div class="h-32 bg-slate-100 rounded-xl animate-pulse" />
      </div>

      <!-- Not found -->
      <div
        v-else-if="!appointment"
        class="bg-white rounded-xl border border-slate-200 p-12 text-center"
      >
        <div class="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-slate-100 mb-3">
          <svg class="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="text-base font-semibold text-slate-900">{{ t('review.appointmentNotFound') }}</p>
        <p class="mt-1 text-sm text-slate-500 max-w-xs mx-auto">
          {{ t('review.appointmentNotFoundDesc') }}
        </p>
        <RouterLink
          to="/customer/appointments"
          class="mt-5 inline-flex items-center gap-1.5 h-10 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
        >
          {{ t('review.viewAppointments') }}
        </RouterLink>
      </div>

      <!-- Success -->
      <div
        v-else-if="submitted"
        class="bg-white rounded-xl border border-slate-200 p-12 flex flex-col items-center text-center"
      >
        <div class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-emerald-50 border border-emerald-100 mb-4">
          <svg class="h-7 w-7 text-emerald-600" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 class="text-xl font-bold text-slate-900 tracking-tight mb-1">{{ t('review.thanks') }}</h2>
        <p class="text-sm text-slate-500">{{ t('review.thanksDesc') }}</p>
      </div>

      <!-- Form -->
      <div v-else class="space-y-5 md:space-y-6">
        <!-- Appointment recap -->
        <div class="bg-white rounded-xl border border-slate-200 p-5 md:p-6">
          <p class="text-sm font-semibold uppercase tracking-wide text-slate-500 mb-2">Appointment</p>
          <p class="text-base font-semibold text-slate-900">{{ appointment.barber_name }}</p>
          <p class="mt-0.5 text-sm text-slate-500">
            {{ formatDate(appointment.date) }} · {{ appointment.start_time.slice(0, 5) }}
          </p>
          <p class="mt-1 text-sm text-slate-500">
            {{ appointment.services.map((s) => s.service_name).join(' · ') }}
          </p>
        </div>

        <!-- Overall rating -->
        <div class="bg-white rounded-xl border border-slate-200 p-5 md:p-6">
          <p class="text-base font-semibold text-slate-900 tracking-tight">
            {{ t('review.overallRating') }}
          </p>

          <div class="mt-4 flex items-center gap-1">
            <button
              v-for="star in 5"
              :key="star"
              type="button"
              class="h-10 w-10 inline-flex items-center justify-center rounded-md transition-transform hover:scale-110 active:scale-95"
              :aria-label="`${star} star${star === 1 ? '' : 's'}`"
              @mouseenter="hoverOverall = star"
              @mouseleave="hoverOverall = 0"
              @click="overallRating = star"
            >
              <svg
                class="h-7 w-7 transition-colors"
                :class="star <= (hoverOverall || overallRating) ? 'text-amber-400 fill-current' : 'text-slate-200 fill-current'"
                viewBox="0 0 20 20"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </button>
            <span v-if="overallRating > 0" class="ml-3 text-sm font-medium text-slate-700">
              {{ ratingLabels[overallRating] }}
            </span>
          </div>
        </div>

        <!-- Per-service ratings -->
        <div
          v-if="serviceRatings.length > 0"
          class="bg-white rounded-xl border border-slate-200 p-5 md:p-6"
        >
          <p class="text-base font-semibold text-slate-900 tracking-tight">
            {{ t('review.perService') }}
            <span class="font-normal text-slate-400">{{ t('auth.register.phoneOptional') }}</span>
          </p>

          <ul class="mt-4 divide-y divide-slate-100">
            <li v-for="(svc, idx) in serviceRatings" :key="idx" class="py-3 flex items-center justify-between gap-3">
              <span class="text-sm font-medium text-slate-900">{{ svc.service_name }}</span>
              <div class="flex items-center gap-0.5">
                <button
                  v-for="star in 5"
                  :key="star"
                  type="button"
                  class="h-8 w-8 inline-flex items-center justify-center rounded-md transition-transform hover:scale-110 active:scale-95"
                  :aria-label="`${star} star${star === 1 ? '' : 's'}`"
                  @mouseenter="svc.hover = star"
                  @mouseleave="svc.hover = 0"
                  @click="svc.rating = star"
                >
                  <svg
                    class="h-5 w-5 transition-colors"
                    :class="star <= (svc.hover || svc.rating) ? 'text-amber-400 fill-current' : 'text-slate-200 fill-current'"
                    viewBox="0 0 20 20"
                  >
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </button>
              </div>
            </li>
          </ul>
        </div>

        <!-- Written review -->
        <div class="bg-white rounded-xl border border-slate-200 p-5 md:p-6">
          <label for="review-text" class="block text-base font-semibold text-slate-900 tracking-tight">
            {{ t('review.reviewLabel') }}
          </label>
          <textarea
            id="review-text"
            v-model="reviewText"
            rows="5"
            :placeholder="t('review.reviewPlaceholder')"
            class="mt-3 w-full px-3.5 py-2.5 rounded-lg border border-slate-200 text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 transition-colors resize-none"
          />
        </div>

        <!-- Error -->
        <div
          v-if="errorMessage"
          class="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
        >
          {{ errorMessage }}
        </div>

        <!-- Submit -->
        <div class="flex flex-col gap-2">
          <button
            type="button"
            class="inline-flex items-center justify-center gap-2 h-11 px-6 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            :disabled="overallRating === 0 || isPending"
            @click="submitReview()"
          >
            <svg v-if="isPending" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
              <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
            </svg>
            {{ isPending ? t('review.submitting') : t('review.submit') }}
          </button>
          <p v-if="overallRating === 0" class="text-sm text-slate-500 text-center">
            {{ t('review.errorRatingRequired') }}
          </p>
        </div>
      </div>
    </section>
  </CustomerLayout>
</template>
