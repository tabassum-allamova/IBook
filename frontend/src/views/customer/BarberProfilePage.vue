<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import api from '@/lib/axios'

const props = defineProps<{
  barberId: string
}>()

const route = useRoute()
const barberIdNum = computed(() => Number(props.barberId))

interface BarberService {
  id: number
  name: string
  price: number
  duration_minutes: number
}

interface WeeklyScheduleEntry {
  day_of_week: number
  is_working: boolean
  start_time: string | null
  end_time: string | null
}

interface BarberProfile {
  id: number
  full_name: string
  avatar: string | null
  bio: string
  years_of_experience: number | null
  services: BarberService[]
  weekly_schedule: WeeklyScheduleEntry[]
  shop_name: string | null
  avg_rating: number | null
}

interface ReviewItem {
  reviewer: string
  rating: number
  text: string
  date: string
}

interface ReviewsData {
  avg_rating: number | null
  total_reviews: number
  distribution: Record<string, number>
  recent_reviews: ReviewItem[]
}

const { data: barber, isLoading, isError } = useQuery({
  queryKey: computed(() => ['barber', barberIdNum.value]),
  queryFn: async () => {
    const res = await api.get<BarberProfile>(`/api/barbers/${barberIdNum.value}/`)
    return res.data
  },
  enabled: computed(() => !isNaN(barberIdNum.value)),
  retry: (failureCount, error: unknown) => {
    const axiosError = error as { response?: { status: number } }
    if (axiosError?.response?.status === 404) return false
    return failureCount < 2
  },
})

const { data: reviewsData, isLoading: isLoadingReviews } = useQuery<ReviewsData>({
  queryKey: computed(() => ['barber-reviews', barberIdNum.value]),
  queryFn: async () => {
    const res = await api.get<ReviewsData>(`/api/reviews/barber/${barberIdNum.value}/`)
    return res.data
  },
  enabled: computed(() => !isNaN(barberIdNum.value) && !!barber.value),
})

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

function formatTime(t: string | null): string {
  if (!t) return ''
  return t.slice(0, 5)
}

function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-US').format(amount) + ' UZS'
}

function getScheduleForDay(schedule: WeeklyScheduleEntry[], dayIndex: number): WeeklyScheduleEntry | undefined {
  return schedule.find((s) => s.day_of_week === dayIndex)
}

// Back link context: if came from a shop detail page, show "Back to Shop"
const backShopId = computed(() => {
  const id = route.query.shopId
  return id ? String(id) : null
})

function formatReviewDate(dateStr: string): string {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function starDistributionPct(count: number, total: number): number {
  if (total === 0) return 0
  return Math.round((count / total) * 100)
}
</script>

<template>
  <CustomerLayout>
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8 pb-24">

      <!-- Back link -->
      <RouterLink
        v-if="backShopId"
        :to="{ name: 'customer-shop-detail', params: { shopId: backShopId } }"
        class="inline-flex items-center gap-1.5 text-sm text-ibook-brown-500 hover:text-ibook-brown-800 transition-colors mb-6"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Shop
      </RouterLink>
      <RouterLink
        v-else
        to="/customer/explore"
        class="inline-flex items-center gap-1.5 text-sm text-ibook-brown-500 hover:text-ibook-brown-800 transition-colors mb-6"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
        </svg>
        Back to Explore
      </RouterLink>

      <!-- Loading skeleton -->
      <div v-if="isLoading" class="space-y-6">
        <div class="flex items-center gap-5">
          <div class="w-24 h-24 rounded-full bg-ibook-brown-100 animate-pulse flex-shrink-0" />
          <div class="flex-1 space-y-3">
            <div class="h-7 bg-ibook-brown-100 rounded animate-pulse w-2/3" />
            <div class="h-4 bg-ibook-brown-50 rounded animate-pulse w-1/3" />
          </div>
        </div>
        <div class="h-24 bg-ibook-brown-100 rounded-xl animate-pulse" />
        <div class="h-40 bg-ibook-brown-100 rounded-xl animate-pulse" />
      </div>

      <!-- Error state -->
      <div
        v-else-if="isError"
        class="flex flex-col items-center justify-center py-20 text-center"
      >
        <svg class="h-12 w-12 text-ibook-brown-300 mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-ibook-brown-700 font-semibold text-lg">Barber not found</p>
        <p class="text-ibook-brown-400 text-sm mt-1">This profile may not exist or the link is invalid.</p>
        <RouterLink
          to="/customer/explore"
          class="mt-4 inline-block py-2 px-4 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          Back to Explore
        </RouterLink>
      </div>

      <!-- Barber content -->
      <div v-else-if="barber" class="space-y-7">

        <!-- Header: avatar, name, experience, shop -->
        <div class="flex items-start gap-5">
          <!-- Avatar -->
          <div class="flex-shrink-0 w-24 h-24 rounded-full overflow-hidden bg-ibook-brown-100 border-2 border-ibook-brown-200">
            <img
              v-if="barber.avatar"
              :src="barber.avatar"
              :alt="barber.full_name"
              class="w-full h-full object-cover"
            />
            <div v-else class="w-full h-full flex items-center justify-center">
              <svg
                class="h-12 w-12 text-ibook-brown-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="1.5"
                  d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                />
              </svg>
            </div>
          </div>

          <!-- Name + meta -->
          <div class="flex-1 pt-1">
            <h1 class="text-2xl font-bold text-ibook-brown-900 mb-1">{{ barber.full_name }}</h1>
            <div class="flex flex-wrap gap-2 mt-2">
              <span
                v-if="barber.years_of_experience !== null"
                class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-ibook-brown-100 text-ibook-brown-700"
              >
                {{ barber.years_of_experience }} {{ barber.years_of_experience === 1 ? 'year' : 'years' }} experience
              </span>
              <span
                v-if="barber.shop_name"
                class="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-ibook-brown-800 text-white"
              >
                at {{ barber.shop_name }}
              </span>
            </div>
          </div>
        </div>

        <!-- Bio -->
        <div class="bg-white rounded-xl border border-ibook-brown-100 shadow-sm p-5">
          <h2 class="text-base font-semibold text-ibook-brown-900 mb-2">About</h2>
          <p v-if="barber.bio" class="text-ibook-brown-700 leading-relaxed text-sm">{{ barber.bio }}</p>
          <p v-else class="text-ibook-brown-400 text-sm italic">No bio provided.</p>
        </div>

        <!-- Services -->
        <div class="bg-white rounded-xl border border-ibook-brown-100 shadow-sm p-5">
          <h2 class="text-base font-semibold text-ibook-brown-900 mb-4">Services</h2>
          <div v-if="barber.services.length > 0" class="divide-y divide-ibook-brown-50">
            <div
              v-for="service in barber.services"
              :key="service.id"
              class="py-3 flex items-center justify-between gap-3"
            >
              <div class="flex-1 min-w-0">
                <p class="font-medium text-ibook-brown-900 text-sm truncate">{{ service.name }}</p>
                <p class="text-xs text-ibook-brown-400 mt-0.5">{{ service.duration_minutes }} min</p>
              </div>
              <span class="flex-shrink-0 text-sm font-semibold text-ibook-brown-800">
                {{ formatPrice(service.price) }}
              </span>
            </div>
          </div>
          <p v-else class="text-ibook-brown-400 text-sm">No services listed.</p>
        </div>

        <!-- Weekly availability -->
        <div class="bg-white rounded-xl border border-ibook-brown-100 shadow-sm p-5">
          <h2 class="text-base font-semibold text-ibook-brown-900 mb-4">Availability</h2>
          <div class="space-y-1">
            <div
              v-for="(day, index) in DAYS"
              :key="index"
              class="flex items-center text-sm py-1.5 border-b border-ibook-brown-50 last:border-0"
            >
              <span class="w-28 font-medium text-ibook-brown-800">{{ day }}</span>
              <span
                v-if="getScheduleForDay(barber.weekly_schedule, index)?.is_working"
                class="text-ibook-brown-600"
              >
                {{ formatTime(getScheduleForDay(barber.weekly_schedule, index)?.start_time ?? null) }} –
                {{ formatTime(getScheduleForDay(barber.weekly_schedule, index)?.end_time ?? null) }}
              </span>
              <span v-else class="text-ibook-brown-400">Off</span>
            </div>
          </div>
        </div>

        <!-- Reviews section -->
        <div class="bg-white rounded-xl border border-ibook-brown-100 shadow-sm p-5">
          <h2 class="text-base font-semibold text-ibook-brown-900 mb-4">Reviews</h2>

          <!-- Reviews loading skeleton -->
          <div v-if="isLoadingReviews" class="space-y-3">
            <div class="h-4 bg-ibook-brown-100 rounded animate-pulse w-1/3" />
            <div class="h-2 bg-ibook-brown-100 rounded animate-pulse" />
            <div class="h-2 bg-ibook-brown-100 rounded animate-pulse w-4/5" />
            <div class="h-2 bg-ibook-brown-100 rounded animate-pulse w-3/4" />
          </div>

          <!-- No reviews yet -->
          <div
            v-else-if="!reviewsData || reviewsData.total_reviews === 0"
            class="text-center py-6"
          >
            <svg class="h-10 w-10 text-ibook-brown-200 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
            </svg>
            <p class="text-ibook-brown-500 font-medium text-sm">No reviews yet</p>
            <p class="text-ibook-brown-400 text-xs mt-1">Be the first to leave a review.</p>
          </div>

          <!-- Reviews content -->
          <div v-else class="space-y-6">

            <!-- Rating summary header -->
            <div class="flex items-center gap-3">
              <div class="flex items-center gap-1.5">
                <span class="text-3xl font-bold text-ibook-brown-900">{{ reviewsData.avg_rating?.toFixed(1) }}</span>
                <svg class="h-7 w-7 text-ibook-gold-400 fill-current" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
              </div>
              <span class="text-sm text-ibook-brown-500">{{ reviewsData.total_reviews }} {{ reviewsData.total_reviews === 1 ? 'review' : 'reviews' }}</span>
            </div>

            <!-- Star distribution bars -->
            <div class="space-y-2">
              <div
                v-for="starNum in [5, 4, 3, 2, 1]"
                :key="starNum"
                class="flex items-center gap-2"
              >
                <span class="w-4 text-xs font-medium text-ibook-brown-600 text-right flex-shrink-0">{{ starNum }}</span>
                <svg class="h-3 w-3 text-ibook-gold-400 fill-current flex-shrink-0" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <div class="flex-1 bg-ibook-brown-100 rounded-full h-2 overflow-hidden">
                  <div
                    class="h-full bg-ibook-gold-400 rounded-full transition-all duration-[600ms] ease-out"
                    :style="{ width: starDistributionPct(reviewsData.distribution[String(starNum)] ?? 0, reviewsData.total_reviews) + '%' }"
                  />
                </div>
                <span class="w-6 text-xs text-ibook-brown-400 text-right flex-shrink-0">
                  {{ reviewsData.distribution[String(starNum)] ?? 0 }}
                </span>
              </div>
            </div>

            <!-- Recent reviews list -->
            <div>
              <p class="text-sm font-semibold text-ibook-brown-900 mb-3">Recent Reviews</p>
              <div class="divide-y divide-ibook-brown-50">
                <div
                  v-for="(review, idx) in reviewsData.recent_reviews"
                  :key="idx"
                  class="py-4 first:pt-0"
                >
                  <div class="flex items-start justify-between mb-1.5">
                    <span class="text-sm font-semibold text-ibook-brown-900">{{ review.reviewer }}</span>
                    <span class="text-xs text-ibook-brown-400 flex-shrink-0 ml-2">{{ formatReviewDate(review.date) }}</span>
                  </div>
                  <!-- Stars -->
                  <div class="flex items-center gap-0.5 mb-2">
                    <svg
                      v-for="star in 5"
                      :key="star"
                      class="h-4 w-4"
                      :class="star <= review.rating ? 'text-ibook-gold-400 fill-current' : 'text-ibook-brown-200 fill-current'"
                      viewBox="0 0 20 20"
                    >
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                  </div>
                  <!-- Review text (only if non-empty) -->
                  <p v-if="review.text" class="text-sm text-ibook-brown-700 leading-relaxed">{{ review.text }}</p>
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>

    <!-- Sticky Book CTA (only when barber loaded) -->
    <div
      v-if="barber && !isLoading && !isError"
      class="fixed bottom-0 left-0 right-0 bg-white border-t border-ibook-brown-100 shadow-lg px-4 py-3 sm:px-6"
    >
      <div class="max-w-3xl mx-auto">
        <RouterLink
          :to="{ name: 'customer-booking', params: { barberId: barber.id } }"
          class="block w-full sm:w-auto sm:mx-auto py-3 px-6 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white font-semibold rounded-xl transition-colors text-center text-base"
        >
          Book with {{ barber.full_name }}
        </RouterLink>
      </div>
    </div>
  </CustomerLayout>
</template>
