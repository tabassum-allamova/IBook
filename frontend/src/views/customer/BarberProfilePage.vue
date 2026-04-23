<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery } from '@tanstack/vue-query'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import api from '@/lib/axios'

const { t, locale } = useI18n()

const BROWSER_LOCALES: Record<string, string> = {
  en: 'en-US',
  ru: 'ru-RU',
  uz: 'uz-UZ',
}

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
  id: number
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

const DAYS = computed(() => [
  t('availability.days.mon'),
  t('availability.days.tue'),
  t('availability.days.wed'),
  t('availability.days.thu'),
  t('availability.days.fri'),
  t('availability.days.sat'),
  t('availability.days.sun'),
])

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
  const tag = BROWSER_LOCALES[locale.value] ?? 'en-US'
  return new Date(dateStr + 'T00:00:00').toLocaleDateString(tag, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function starDistributionPct(count: number, total: number): number {
  if (total === 0) return 0
  return Math.round((count / total) * 100)
}

const todayIndex = computed(() => {
  const jsDay = new Date().getDay()
  return (jsDay + 6) % 7
})
</script>

<template>
  <CustomerLayout>
    <!-- Back button -->
    <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-5">
      <RouterLink
        v-if="backShopId"
        :to="{ name: 'customer-shop-detail', params: { shopId: backShopId } }"
        class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        {{ t('shopDetail.backToShops') }}
      </RouterLink>
      <RouterLink
        v-else
        to="/customer/explore"
        class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        {{ t('shopDetail.backToShops') }}
      </RouterLink>
    </div>

    <!-- Loading skeleton -->
    <div v-if="isLoading" class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-6 pb-16">
      <div class="flex items-center gap-4 md:gap-5">
        <div class="h-14 w-14 md:h-16 md:w-16 bg-slate-100 animate-pulse rounded-xl flex-shrink-0" />
        <div class="flex-1 space-y-2.5">
          <div class="h-7 w-1/2 bg-slate-100 animate-pulse rounded" />
          <div class="h-4 w-1/3 bg-slate-100 animate-pulse rounded" />
        </div>
      </div>
    </div>

    <!-- Error state -->
    <div
      v-else-if="isError"
      class="max-w-2xl mx-auto px-5 md:px-8 py-24 text-center"
    >
      <p class="text-sm uppercase tracking-wide font-semibold text-slate-400 mb-2">404</p>
      <h1 class="text-2xl md:text-3xl font-bold text-slate-900 mb-3 tracking-tight">{{ t('shopDetail.notFoundTitle').replace('Shop', 'Barber') }}</h1>
      <p class="text-slate-600 mb-6">
        {{ t('shopDetail.notFoundDesc') }}
      </p>
      <RouterLink
        to="/customer/explore"
        class="inline-flex items-center gap-1 px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white font-semibold text-sm transition-colors"
      >
        {{ t('shopDetail.backToShops') }}
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </RouterLink>
    </div>

    <!-- Content -->
    <template v-else-if="barber">
      <!-- Identity row: avatar + name + meta + CTA -->
      <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-6 md:pt-8">
        <div class="flex items-start md:items-center gap-4 md:gap-5 flex-wrap md:flex-nowrap">
          <!-- Avatar -->
          <div
            class="flex-shrink-0 h-14 w-14 md:h-16 md:w-16 rounded-xl overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center"
          >
            <img
              v-if="barber.avatar"
              :src="barber.avatar"
              :alt="barber.full_name"
              class="w-full h-full object-cover"
            />
            <svg
              v-else
              class="h-8 w-8 text-slate-300"
              fill="none"
              stroke="currentColor"
              stroke-width="1.4"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>

          <!-- Title + meta -->
          <div class="flex-1 min-w-0">
            <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight truncate">
              {{ barber.full_name }}
            </h1>
            <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-600">
              <span v-if="barber.shop_name" class="inline-flex items-center gap-1.5">
                <svg class="h-4 w-4 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
                </svg>
                <span>at <span class="font-medium text-slate-900">{{ barber.shop_name }}</span></span>
              </span>
              <span
                v-if="barber.shop_name && barber.years_of_experience !== null"
                class="text-slate-300" aria-hidden="true">·</span>
              <span v-if="barber.years_of_experience !== null">
                {{ t('barberProfile.yearsExperience', { count: barber.years_of_experience }, barber.years_of_experience) }}
              </span>
              <span
                v-if="
                  (barber.shop_name || barber.years_of_experience !== null) &&
                  reviewsData && reviewsData.avg_rating !== null
                "
                class="text-slate-300" aria-hidden="true">·</span>
              <span v-if="reviewsData && reviewsData.avg_rating !== null" class="inline-flex items-center gap-1">
                <svg class="h-4 w-4 text-amber-400 fill-current" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                <span class="font-medium text-slate-900">{{ reviewsData.avg_rating.toFixed(1) }}</span>
                <span class="text-slate-500">({{ reviewsData.total_reviews }})</span>
              </span>
            </div>
          </div>

          <!-- CTA -->
          <RouterLink
            :to="{ name: 'customer-booking', params: { barberId: barber.id } }"
            class="w-full md:w-auto flex-shrink-0 inline-flex items-center justify-center gap-1 px-5 h-11 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
          >
            {{ t('shopDetail.book') }}
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </RouterLink>
        </div>
      </section>

      <!-- Content -->
      <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-10 md:py-12">
        <div class="grid md:grid-cols-3 gap-8 md:gap-10">
          <!-- Left col: Services + Reviews -->
          <div class="md:col-span-2 space-y-10">
            <!-- Services -->
            <div>
              <h2 class="text-lg font-semibold text-slate-900 mb-3 tracking-tight">{{ t('barberProfile.services') }}</h2>
              <div
                v-if="barber.services.length > 0"
                class="rounded-xl border border-slate-200 overflow-hidden bg-white"
              >
                <div
                  v-for="(service, i) in barber.services"
                  :key="service.id"
                  :class="[
                    'flex items-center justify-between gap-4 px-5 py-4',
                    i < barber.services.length - 1 ? 'border-b border-slate-100' : '',
                  ]"
                >
                  <div class="min-w-0">
                    <p class="text-base font-semibold text-slate-900">{{ service.name }}</p>
                    <p class="text-sm text-slate-500 mt-0.5">{{ service.duration_minutes }} {{ t('booking.summary.minutes') }}</p>
                  </div>
                  <p class="text-sm font-semibold text-slate-900 tabular-nums whitespace-nowrap flex-shrink-0">
                    {{ formatPrice(service.price) }}
                  </p>
                </div>
              </div>
              <p v-else class="text-slate-400 text-[15px]">
                No services listed yet.
              </p>
            </div>

            <!-- Reviews -->
            <div>
              <h2 class="text-lg font-semibold text-slate-900 mb-3 tracking-tight">{{ t('barberProfile.reviews') }}</h2>

              <!-- Loading skeleton -->
              <div v-if="isLoadingReviews" class="space-y-3">
                <div class="h-8 bg-slate-100 rounded animate-pulse w-1/3" />
                <div class="h-2 bg-slate-100 rounded animate-pulse" />
                <div class="h-2 bg-slate-100 rounded animate-pulse w-4/5" />
              </div>

              <!-- No reviews -->
              <div
                v-else-if="!reviewsData || reviewsData.total_reviews === 0"
                class="bg-white rounded-xl border border-slate-200 p-6"
              >
                <p class="text-[15px] text-slate-700 mb-0.5">{{ t('barberProfile.noReviews') }}</p>
                <p class="text-sm text-slate-500">{{ t('barberProfile.noReviews') }}</p>
              </div>

              <!-- Reviews content -->
              <div v-else class="space-y-6">
                <!-- Summary + distribution -->
                <div class="bg-white rounded-xl border border-slate-200 p-5 md:p-6">
                  <div class="flex items-start gap-6 md:gap-10">
                    <div class="flex-shrink-0">
                      <div class="text-4xl md:text-5xl font-bold text-slate-900 leading-none tabular-nums">
                        {{ reviewsData.avg_rating?.toFixed(1) }}
                      </div>
                      <div class="mt-2 flex items-center gap-0.5">
                        <svg
                          v-for="star in 5"
                          :key="star"
                          class="h-4 w-4"
                          :class="star <= Math.round(reviewsData.avg_rating ?? 0) ? 'text-amber-400 fill-current' : 'text-slate-200 fill-current'"
                          viewBox="0 0 20 20"
                        >
                          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                        </svg>
                      </div>
                      <p class="mt-1 text-sm text-slate-500">
                        {{ t('dashboard.subline.reviews', { count: reviewsData.total_reviews }, reviewsData.total_reviews) }}
                      </p>
                    </div>
                    <div class="flex-1 space-y-1.5 min-w-0">
                      <div
                        v-for="starNum in [5, 4, 3, 2, 1]"
                        :key="starNum"
                        class="flex items-center gap-3"
                      >
                        <span class="w-3 text-sm font-medium text-slate-600 text-right">{{ starNum }}</span>
                        <div class="flex-1 bg-slate-100 rounded-full h-1.5 overflow-hidden">
                          <div
                            class="h-full bg-amber-400 rounded-full transition-all duration-[600ms] ease-out"
                            :style="{ width: starDistributionPct(reviewsData.distribution[String(starNum)] ?? 0, reviewsData.total_reviews) + '%' }"
                          />
                        </div>
                        <span class="w-6 text-sm text-slate-500 text-right tabular-nums">
                          {{ reviewsData.distribution[String(starNum)] ?? 0 }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- Recent reviews -->
                <div
                  v-if="reviewsData.recent_reviews.length > 0"
                  class="rounded-xl border border-slate-200 overflow-hidden bg-white"
                >
                  <div
                    v-for="(review, idx) in reviewsData.recent_reviews"
                    :key="review.id"
                    :class="[
                      'px-5 py-4',
                      idx < reviewsData.recent_reviews.length - 1 ? 'border-b border-slate-100' : '',
                    ]"
                  >
                    <div class="flex items-center justify-between gap-3 mb-1.5">
                      <div class="flex items-center gap-2 min-w-0">
                        <span class="text-sm font-semibold text-slate-900 truncate">{{ review.reviewer }}</span>
                        <div class="flex items-center gap-0.5 flex-shrink-0">
                          <svg
                            v-for="star in 5"
                            :key="star"
                            class="h-3 w-3"
                            :class="star <= review.rating ? 'text-amber-400 fill-current' : 'text-slate-200 fill-current'"
                            viewBox="0 0 20 20"
                          >
                            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                          </svg>
                        </div>
                      </div>
                      <span class="text-sm text-slate-500 flex-shrink-0">{{ formatReviewDate(review.date) }}</span>
                    </div>
                    <p v-if="review.text" class="text-sm text-slate-700 leading-relaxed">
                      {{ review.text }}
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Right aside: About + Schedule -->
          <aside class="space-y-8">
            <!-- About -->
            <div v-if="barber.bio">
              <h2 class="text-lg font-semibold text-slate-900 mb-3 tracking-tight">{{ t('shopDetail.about') }}</h2>
              <p class="text-[15px] text-slate-700 leading-relaxed">
                {{ barber.bio }}
              </p>
            </div>

            <!-- Weekly schedule -->
            <div>
              <h2 class="text-lg font-semibold text-slate-900 mb-3 tracking-tight">{{ t('availability.weeklySchedule') }}</h2>
              <dl class="text-[15px] rounded-xl border border-slate-200 overflow-hidden bg-white">
                <div
                  v-for="(day, i) in DAYS"
                  :key="i"
                  :class="[
                    'flex items-center justify-between py-2.5 px-4',
                    i < DAYS.length - 1 ? 'border-b border-slate-100' : '',
                    i === todayIndex ? 'bg-slate-50' : 'bg-white',
                  ]"
                >
                  <dt class="text-slate-900 font-medium flex items-center gap-2">
                    {{ day }}
                    <span v-if="i === todayIndex" class="text-sm font-medium text-slate-500">{{ t('shopDetail.today') }}</span>
                  </dt>
                  <dd class="text-slate-600 tabular-nums text-right">
                    <template v-if="getScheduleForDay(barber.weekly_schedule, i)?.is_working">
                      {{ formatTime(getScheduleForDay(barber.weekly_schedule, i)?.start_time ?? null) }}
                      <span class="text-slate-300 mx-1">–</span>
                      {{ formatTime(getScheduleForDay(barber.weekly_schedule, i)?.end_time ?? null) }}
                    </template>
                    <span v-else class="text-slate-400">{{ t('availability.dayOff') }}</span>
                  </dd>
                </div>
              </dl>
            </div>
          </aside>
        </div>
      </section>
    </template>

    <!-- Sticky mobile Book CTA -->
    <div
      v-if="barber && !isLoading && !isError"
      class="md:hidden fixed left-0 right-0 z-40 bg-white/95 backdrop-blur border-t border-slate-200 px-4 py-3"
      style="bottom: 56px; padding-bottom: calc(12px + env(safe-area-inset-bottom, 0px));"
    >
      <RouterLink
        :to="{ name: 'customer-booking', params: { barberId: barber.id } }"
        class="flex items-center justify-center gap-2 w-full h-11 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
      >
        Book with {{ barber.full_name.split(' ')[0] }}
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </RouterLink>
    </div>
  </CustomerLayout>
</template>
