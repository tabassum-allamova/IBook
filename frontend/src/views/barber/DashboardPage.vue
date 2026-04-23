<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useQuery } from '@tanstack/vue-query'
import BaseModal from '@/components/ui/BaseModal.vue'

const { t, locale } = useI18n()

const BROWSER_LOCALES: Record<string, string> = {
  en: 'en-US',
  ru: 'ru-RU',
  uz: 'uz-UZ',
}

import { Line, Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js'
import BarberLayout from '@/layouts/BarberLayout.vue'
import api from '@/lib/axios'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
)

interface SeriesPoint {
  day: string
  count: number
  revenue: number
}
interface ServiceRow {
  name: string
  count: number
  revenue: number
}
interface DowRow {
  day_of_week: number
  count: number
  revenue: number
}
interface HodRow {
  hour: number
  count: number
}
interface ReviewItem {
  reviewer: string
  rating: number
  text: string
  date: string
}

interface AnalyticsData {
  total_bookings: number
  total_revenue: number
  avg_ticket: number
  previous: { total_bookings: number; total_revenue: number }
  series: SeriesPoint[]
  forecast: SeriesPoint[]
  top_services: ServiceRow[]
  day_of_week: DowRow[]
  hour_of_day: HodRow[]
  status_breakdown: {
    completed: number
    confirmed: number
    cancelled: number
    no_show: number
  }
  completion_rate: number | null
  unique_customers: number
  repeat_customers: number
  repeat_rate: number | null
  ratings: {
    avg: number | null
    count: number
    distribution: Record<string, number>
    recent: ReviewItem[]
  }
}

const periods = computed(() => [
  { label: t('dashboard.periods.7d'), value: '7d' },
  { label: t('dashboard.periods.30d'), value: '30d' },
  { label: t('dashboard.periods.90d'), value: '90d' },
  { label: t('dashboard.periods.all'), value: 'all' },
])

const period = ref('30d')

const { data, isLoading } = useQuery<AnalyticsData>({
  queryKey: computed(() => ['barber-analytics', period.value]),
  queryFn: () =>
    api
      .get<AnalyticsData>('/api/bookings/analytics/barber/', { params: { period: period.value } })
      .then((r) => r.data),
})

// ---- Formatting ----
function formatDate(iso: string): string {
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
function formatPrice(n: number): string {
  return new Intl.NumberFormat('en-US').format(n) + ' UZS'
}
function formatCount(n: number): string {
  return new Intl.NumberFormat('en-US').format(n)
}
function pctChange(current: number, previous: number): number | null {
  if (previous === 0) return current === 0 ? 0 : null
  return ((current - previous) / previous) * 100
}
function formatHour(h: number): string {
  const tag = BROWSER_LOCALES[locale.value] ?? 'en-US'
  const d = new Date()
  d.setHours(h, 0, 0, 0)
  return d.toLocaleTimeString(tag, { hour: 'numeric' })
}
function formatReviewDate(iso: string): string {
  const tag = BROWSER_LOCALES[locale.value] ?? 'en-US'
  return new Date(iso + 'T00:00:00').toLocaleDateString(tag, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

const bookingsDelta = computed(() => {
  if (!data.value) return null
  return pctChange(data.value.total_bookings, data.value.previous.total_bookings)
})
const revenueDelta = computed(() => {
  if (!data.value) return null
  return pctChange(data.value.total_revenue, data.value.previous.total_revenue)
})

// ---- Metric detail modal ----
type MetricKey =
  | 'total_bookings'
  | 'revenue'
  | 'avg_ticket'
  | 'avg_rating'
  | 'completion_rate'
  | 'repeat_customers'
  | 'unique_customers'
  | 'forecast_bookings'
  | 'forecast_revenue'

interface MetricInfo {
  title: string
  what: string
  howLines: string[]
  why: string
  eyebrow?: string
}

const METRIC_INFO: Record<MetricKey, MetricInfo> = {
  total_bookings: {
    title: 'Total bookings',
    what: 'The number of appointments you delivered or have confirmed in the selected period.',
    howLines: [
      'Counts appointments with status Completed or Confirmed, dated on or before today, within the selected period.',
      'The % below compares this window to the previous equal-length window.',
    ],
    why: 'Top-line volume — how busy you were. A rising number usually means stronger demand or more available hours on your schedule.',
  },
  revenue: {
    title: 'Revenue',
    what: 'Total earnings from the bookings counted above.',
    howLines: [
      'Sum of the total price of every Completed or Confirmed appointment in the selected period.',
      'Platform fees and refunds are not deducted — this is gross booking value in UZS.',
    ],
    why: "Moves with both price and volume. If bookings grow but revenue doesn't, customers are choosing cheaper services.",
  },
  avg_ticket: {
    title: 'Average ticket',
    what: 'Average spend per booking in the selected period.',
    howLines: ['Revenue ÷ Total bookings.'],
    why: 'A rising ticket usually means a better service mix or successful upsells. A falling ticket means customers are shifting to cheaper options.',
  },
  avg_rating: {
    title: 'Average rating',
    what: "Mean star rating across every review you've received.",
    howLines: [
      'Average of 1–5 star ratings left by customers after an appointment.',
      'Covers all reviews you have ever received — not limited to the selected period — so the number moves slowly.',
    ],
    why: "Core customer-satisfaction signal. It's also used when ranking barbers in search results, so it directly affects discovery.",
  },
  completion_rate: {
    title: 'Completion rate',
    what: 'Share of your bookings that actually went ahead vs. ended in cancellation or no-show.',
    howLines: [
      'Completed ÷ (Completed + Confirmed + Cancelled + No-show) within the selected period.',
      "Uses every booking in the window — including cancelled and no-show ones — so cancellations are visible here even though they don't appear in Total bookings.",
    ],
    why: 'A drop often points to scheduling gaps, slow confirmation, or unclear expectations. A high completion rate is a reliability signal to returning customers.',
  },
  repeat_customers: {
    title: 'Repeat customers',
    what: 'How much of your work comes from customers who booked you more than once.',
    howLines: [
      'The large % = bookings from returning customers ÷ total bookings.',
      'The line below = how many individual customers came back out of your unique customers.',
    ],
    why: 'Loyalty signal. Repeat business is usually more profitable than new-customer acquisition, and a healthy repeat rate protects you when demand dips.',
  },
  unique_customers: {
    title: 'Unique customers',
    what: 'Number of distinct customers you served in the selected period.',
    howLines: ['Counts each customer once, no matter how many times they booked you.'],
    why: "Reach — how many different people you're working with. Compare with Total bookings to see whether your volume is coming from many customers or a loyal few.",
  },
  forecast_bookings: {
    title: '7-day booking forecast',
    eyebrow: 'Next 7 days',
    what: "An estimate of how many bookings you'll take across the next 7 days, based on your recent pace. The dashed line on the chart shows the same projection day by day.",
    howLines: [
      'Takes the last 14 days of booking activity, zero-filled for days with none.',
      'Applies an exponentially-weighted moving average — the most recent days count much more than older ones — and projects that daily average flat across the next 7 days.',
    ],
    why: 'A quick planning signal for the week ahead. A dry stretch at the tail of the window (including days you were off) will pull this number down, so treat it as a baseline, not a promise.',
  },
  forecast_revenue: {
    title: '7-day revenue forecast',
    eyebrow: 'Next 7 days',
    what: "An estimate of the revenue you'll earn across the next 7 days.",
    howLines: [
      'Same moving-average method as the booking forecast, applied to daily revenue instead of booking counts.',
      'Uses the last 14 days of per-day revenue, exponentially weighted toward the most recent days, projected flat across 7 days.',
    ],
    why: 'A rough cashflow marker for the coming week. Because recency is weighted heavily and recent zero days count as zero demand, compare against your longer-term average before making decisions.',
  },
}

const activeMetric = ref<MetricKey | null>(null)
const activeMetricInfo = computed(() =>
  activeMetric.value ? METRIC_INFO[activeMetric.value] : null,
)
const periodLabel = computed(
  () => periods.value.find((p) => p.value === period.value)?.label.toLowerCase() ?? period.value,
)

const activeMetricValueDisplay = computed(() => {
  const d = data.value
  const key = activeMetric.value
  if (!d || !key) return ''
  switch (key) {
    case 'total_bookings':
      return formatCount(d.total_bookings)
    case 'revenue':
      return formatPrice(d.total_revenue)
    case 'avg_ticket':
      return formatPrice(d.avg_ticket)
    case 'avg_rating':
      return d.ratings.avg !== null ? d.ratings.avg.toFixed(1) : '—'
    case 'completion_rate':
      return d.completion_rate !== null ? `${d.completion_rate}%` : '—'
    case 'repeat_customers':
      return d.repeat_rate !== null ? `${d.repeat_rate}%` : '—'
    case 'unique_customers':
      return formatCount(d.unique_customers)
    case 'forecast_bookings':
      return formatCount(Math.round(forecastTotal.value.bookings))
    case 'forecast_revenue':
      return formatPrice(forecastTotal.value.revenue)
  }
})

const activeMetricSublineDisplay = computed(() => {
  const d = data.value
  const key = activeMetric.value
  if (!d || !key) return ''
  switch (key) {
    case 'total_bookings': {
      const delta = bookingsDelta.value
      if (delta === null) return t('dashboard.subline.noPrior')
      const sign = delta >= 0 ? '+' : '−'
      return `${sign}${Math.abs(delta).toFixed(1)}% ${t('dashboard.subline.vsPrevious')} ${periodLabel.value}`
    }
    case 'revenue': {
      const delta = revenueDelta.value
      if (delta === null) return t('dashboard.subline.noPrior')
      const sign = delta >= 0 ? '+' : '−'
      return `${sign}${Math.abs(delta).toFixed(1)}% ${t('dashboard.subline.vsPrevious')} ${periodLabel.value}`
    }
    case 'avg_ticket':
      return t('dashboard.subline.across', { count: d.total_bookings }, d.total_bookings)
    case 'avg_rating':
      return `${t('dashboard.subline.reviews', { count: d.ratings.count }, d.ratings.count)} · ${t('dashboard.allTime')}`
    case 'completion_rate': {
      const sb = d.status_breakdown
      const parts: string[] = [t('dashboard.subline.completed', { count: sb.completed })]
      if (sb.confirmed > 0) parts.push(t('dashboard.outcomeUpcoming'))
      if (sb.cancelled > 0) parts.push(t('dashboard.subline.cancelled', { count: sb.cancelled }))
      if (sb.no_show > 0) parts.push(t('dashboard.subline.noShow', { count: sb.no_show }))
      return parts.join(' · ')
    }
    case 'repeat_customers':
      return t('dashboard.subline.repeatLine', { repeat: d.repeat_customers, unique: d.unique_customers }, d.unique_customers)
    case 'unique_customers':
      return t('dashboard.subline.inPeriod')
    case 'forecast_bookings': {
      const perDay = forecastTotal.value.bookings / 7
      return t('dashboard.subline.perDayBookings', { avg: perDay.toFixed(2) })
    }
    case 'forecast_revenue': {
      const perDay = Math.round(forecastTotal.value.revenue / 7)
      return t('dashboard.subline.perDayRevenue', { price: formatPrice(perDay) })
    }
  }
})

function openMetric(key: MetricKey) {
  activeMetric.value = key
}
function closeMetric() {
  activeMetric.value = null
}

// ---- Trend + forecast chart ----
const trendChartData = computed(() => {
  if (!data.value) return { labels: [], datasets: [] }
  const history = data.value.series ?? []
  const forecast = data.value.forecast ?? []
  const labels = [...history.map((d) => formatDate(d.day)), ...forecast.map((d) => formatDate(d.day))]

  const histData: (number | null)[] = history.map((d) => d.count)
  histData.push(...forecast.map(() => null))

  const forecastData: (number | null)[] = history.map(() => null)
  if (history.length > 0) forecastData[history.length - 1] = history[history.length - 1].count
  forecastData.push(...forecast.map((d) => d.count))

  return {
    labels,
    datasets: [
      {
        label: 'Bookings',
        data: histData,
        borderColor: '#0f172a',
        backgroundColor: 'rgba(15, 23, 42, 0.06)',
        tension: 0.35,
        fill: true,
        pointBackgroundColor: '#0f172a',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        spanGaps: false,
      },
      {
        label: 'Forecast',
        data: forecastData,
        borderColor: '#0f172a',
        borderDash: [6, 4],
        backgroundColor: 'rgba(15, 23, 42, 0.03)',
        tension: 0.35,
        fill: true,
        pointBackgroundColor: '#94a3b8',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
        spanGaps: false,
      },
    ],
  }
})

const trendChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: true,
      position: 'bottom' as const,
      labels: { color: '#475569', font: { size: 12 }, usePointStyle: true, padding: 16 },
    },
    tooltip: {
      backgroundColor: '#0f172a',
      padding: 10,
      cornerRadius: 8,
      titleFont: { size: 12, weight: 600 },
      bodyFont: { size: 12 },
      displayColors: false,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { precision: 0, color: '#94a3b8', font: { size: 12 } },
      grid: { color: 'rgba(15, 23, 42, 0.05)' },
      border: { display: false },
    },
    x: {
      grid: { display: false },
      ticks: { color: '#94a3b8', font: { size: 12 }, maxRotation: 0, autoSkipPadding: 20 },
      border: { display: false },
    },
  },
}

// ---- Day of week bar chart ----
const DAY_NAMES = computed(() => [
  t('availability.days.mon').slice(0, 3),
  t('availability.days.tue').slice(0, 3),
  t('availability.days.wed').slice(0, 3),
  t('availability.days.thu').slice(0, 3),
  t('availability.days.fri').slice(0, 3),
  t('availability.days.sat').slice(0, 3),
  t('availability.days.sun').slice(0, 3),
])
const dowChartData = computed(() => {
  const rows = data.value?.day_of_week ?? []
  return {
    labels: DAY_NAMES.value,
    datasets: [
      {
        label: t('dashboard.metrics.totalBookings'),
        data: rows.map((r) => r.count),
        backgroundColor: '#0f172a',
        borderRadius: 6,
        maxBarThickness: 40,
      },
    ],
  }
})

const dowChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: '#0f172a',
      padding: 10,
      cornerRadius: 8,
      titleFont: { size: 12, weight: 600 },
      bodyFont: { size: 12 },
      displayColors: false,
    },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { precision: 0, color: '#94a3b8', font: { size: 12 } },
      grid: { color: 'rgba(15, 23, 42, 0.05)' },
      border: { display: false },
    },
    x: {
      grid: { display: false },
      ticks: { color: '#475569', font: { size: 12 } },
      border: { display: false },
    },
  },
}

// ---- Peak hours ----
const peakHours = computed(() => {
  const rows = data.value?.hour_of_day ?? []
  const max = rows.reduce((m, r) => (r.count > m ? r.count : m), 0)
  return { rows, max }
})

// ---- Forecast summary ----
const forecastTotal = computed(() => {
  if (!data.value?.forecast) return { bookings: 0, revenue: 0 }
  return data.value.forecast.reduce(
    (acc, r) => ({ bookings: acc.bookings + r.count, revenue: acc.revenue + r.revenue }),
    { bookings: 0, revenue: 0 },
  )
})

// ---- Top services ----
const topServices = computed(() => data.value?.top_services ?? [])
const maxServiceCount = computed(() =>
  topServices.value.reduce((m, s) => (s.count > m ? s.count : m), 0),
)

// ---- Outcome slice ----
const outcomeTotal = computed(() => {
  const sb = data.value?.status_breakdown
  if (!sb) return 0
  return sb.completed + sb.confirmed + sb.cancelled + sb.no_show
})

function statusPct(n: number): string {
  const t = outcomeTotal.value
  if (t === 0) return '0%'
  return `${((n / t) * 100).toFixed(0)}%`
}

// ---- Ratings ----
const ratingDistRows = computed(() => {
  const dist = data.value?.ratings.distribution ?? {}
  const total = data.value?.ratings.count ?? 0
  return [5, 4, 3, 2, 1].map((star) => ({
    star,
    count: dist[String(star)] ?? 0,
    pct: total > 0 ? Math.round(((dist[String(star)] ?? 0) * 100) / total) : 0,
  }))
})
</script>

<template>
  <BarberLayout>
    <section class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
            {{ t('dashboard.title') }}
          </h1>
          <p class="mt-1 text-sm text-slate-600">
            {{ t('dashboard.subtitle') }}
          </p>
        </div>

        <!-- Period picker -->
        <div
          role="tablist"
          :aria-label="t('dashboard.periodAria')"
          class="inline-flex items-center h-10 rounded-lg border border-slate-200 bg-white p-0.5 flex-shrink-0 self-start sm:self-auto"
        >
          <button
            v-for="p in periods"
            :key="p.value"
            type="button"
            role="tab"
            :aria-selected="period === p.value"
            :class="[
              'inline-flex items-center h-full px-3.5 text-sm font-medium rounded-md transition-colors',
              period === p.value
                ? 'bg-slate-900 text-white'
                : 'text-slate-600 hover:text-slate-900',
            ]"
            @click="period = p.value"
          >
            {{ p.label }}
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="isLoading" class="space-y-5">
        <div class="grid grid-cols-1 sm:grid-cols-4 gap-4 md:gap-5">
          <div v-for="i in 4" :key="i" class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="h-4 w-1/3 bg-slate-100 animate-pulse rounded mb-3" />
            <div class="h-8 w-1/2 bg-slate-100 animate-pulse rounded" />
          </div>
        </div>
        <div class="bg-white rounded-xl border border-slate-200 p-6">
          <div class="h-64 bg-slate-100 animate-pulse rounded" />
        </div>
      </div>

      <template v-else-if="data">
        <!-- KPI cards -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-5 mb-5 md:mb-6">
          <button
            type="button"
            class="bg-white rounded-xl border border-slate-200 p-6 w-full text-left relative group cursor-pointer hover:border-slate-300 hover:shadow-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70 focus-visible:ring-offset-2"
            @click="openMetric('total_bookings')"
          >
            <span class="absolute top-3.5 right-3.5 text-slate-300 group-hover:text-slate-500 transition-colors" aria-hidden="true">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
              </svg>
            </span>
            <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.totalBookings') }}</p>
            <p class="text-3xl font-bold text-slate-900 tracking-tight tabular-nums">
              {{ formatCount(data.total_bookings) }}
            </p>
            <p v-if="bookingsDelta !== null" class="mt-2 text-sm">
              <span
                class="inline-flex items-center gap-1 font-medium"
                :class="bookingsDelta >= 0 ? 'text-emerald-700' : 'text-red-600'"
              >
                <svg
                  class="h-3.5 w-3.5"
                  :class="bookingsDelta >= 0 ? '' : 'rotate-180'"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                </svg>
                {{ Math.abs(bookingsDelta).toFixed(1) }}%
              </span>
              <span class="text-slate-500"> {{ t('dashboard.subline.vsPrevious') }}</span>
            </p>
            <p v-else class="mt-2 text-sm text-slate-500">{{ t('dashboard.subline.noPrior') }}</p>
          </button>

          <button
            type="button"
            class="bg-white rounded-xl border border-slate-200 p-6 w-full text-left relative group cursor-pointer hover:border-slate-300 hover:shadow-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70 focus-visible:ring-offset-2"
            @click="openMetric('revenue')"
          >
            <span class="absolute top-3.5 right-3.5 text-slate-300 group-hover:text-slate-500 transition-colors" aria-hidden="true">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
              </svg>
            </span>
            <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.revenue') }}</p>
            <p class="text-3xl font-bold text-slate-900 tracking-tight tabular-nums">
              {{ formatPrice(data.total_revenue) }}
            </p>
            <p v-if="revenueDelta !== null" class="mt-2 text-sm">
              <span
                class="inline-flex items-center gap-1 font-medium"
                :class="revenueDelta >= 0 ? 'text-emerald-700' : 'text-red-600'"
              >
                <svg
                  class="h-3.5 w-3.5"
                  :class="revenueDelta >= 0 ? '' : 'rotate-180'"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2.2"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M5 15l7-7 7 7" />
                </svg>
                {{ Math.abs(revenueDelta).toFixed(1) }}%
              </span>
              <span class="text-slate-500"> {{ t('dashboard.subline.vsPrevious') }}</span>
            </p>
            <p v-else class="mt-2 text-sm text-slate-500">{{ t('dashboard.subline.noPrior') }}</p>
          </button>

          <button
            type="button"
            class="bg-white rounded-xl border border-slate-200 p-6 w-full text-left relative group cursor-pointer hover:border-slate-300 hover:shadow-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70 focus-visible:ring-offset-2"
            @click="openMetric('avg_ticket')"
          >
            <span class="absolute top-3.5 right-3.5 text-slate-300 group-hover:text-slate-500 transition-colors" aria-hidden="true">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
              </svg>
            </span>
            <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.avgTicket') }}</p>
            <p class="text-3xl font-bold text-slate-900 tracking-tight tabular-nums">
              {{ formatPrice(data.avg_ticket) }}
            </p>
            <p class="mt-2 text-sm text-slate-500">
              {{ t('dashboard.subline.across', { count: data.total_bookings }, data.total_bookings) }}
            </p>
          </button>

          <button
            type="button"
            class="bg-white rounded-xl border border-slate-200 p-6 w-full text-left relative group cursor-pointer hover:border-slate-300 hover:shadow-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70 focus-visible:ring-offset-2"
            @click="openMetric('avg_rating')"
          >
            <span class="absolute top-3.5 right-3.5 text-slate-300 group-hover:text-slate-500 transition-colors" aria-hidden="true">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
              </svg>
            </span>
            <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.avgRating') }}</p>
            <div class="flex items-baseline gap-2">
              <p class="text-3xl font-bold text-slate-900 tracking-tight tabular-nums">
                {{ data.ratings.avg?.toFixed(1) ?? '—' }}
              </p>
              <svg
                v-if="data.ratings.avg !== null"
                class="h-5 w-5 text-amber-400 fill-current"
                viewBox="0 0 20 20"
              >
                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
              </svg>
            </div>
            <p class="mt-2 text-sm text-slate-500">
              {{ t('dashboard.subline.reviews', { count: data.ratings.count }, data.ratings.count) }}
            </p>
          </button>
        </div>

        <!-- Secondary KPIs: completion + repeat customers -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-5 mb-5 md:mb-6">
          <button
            type="button"
            class="bg-white rounded-xl border border-slate-200 p-6 w-full text-left relative group cursor-pointer hover:border-slate-300 hover:shadow-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70 focus-visible:ring-offset-2"
            @click="openMetric('completion_rate')"
          >
            <span class="absolute top-3.5 right-3.5 text-slate-300 group-hover:text-slate-500 transition-colors" aria-hidden="true">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
              </svg>
            </span>
            <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.completionRate') }}</p>
            <p class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight tabular-nums">
              {{ data.completion_rate !== null ? `${data.completion_rate}%` : '—' }}
            </p>
            <p class="mt-2 text-sm text-slate-500">
              {{ t('dashboard.subline.completed', { count: data.status_breakdown.completed }) }}
              <span v-if="data.status_breakdown.cancelled > 0">
                · {{ t('dashboard.subline.cancelled', { count: data.status_breakdown.cancelled }) }}
              </span>
              <span v-if="data.status_breakdown.no_show > 0">
                · {{ t('dashboard.subline.noShow', { count: data.status_breakdown.no_show }) }}
              </span>
            </p>
          </button>

          <button
            type="button"
            class="bg-white rounded-xl border border-slate-200 p-6 w-full text-left relative group cursor-pointer hover:border-slate-300 hover:shadow-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70 focus-visible:ring-offset-2"
            @click="openMetric('repeat_customers')"
          >
            <span class="absolute top-3.5 right-3.5 text-slate-300 group-hover:text-slate-500 transition-colors" aria-hidden="true">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
              </svg>
            </span>
            <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.repeatCustomers') }}</p>
            <p class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight tabular-nums">
              {{ data.repeat_rate !== null ? `${data.repeat_rate}%` : '—' }}
            </p>
            <p class="mt-2 text-sm text-slate-500">
              {{ t('dashboard.subline.repeatLine', { repeat: data.repeat_customers, unique: data.unique_customers }, data.unique_customers) }}
            </p>
          </button>

          <button
            type="button"
            class="bg-white rounded-xl border border-slate-200 p-6 w-full text-left relative group cursor-pointer hover:border-slate-300 hover:shadow-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70 focus-visible:ring-offset-2"
            @click="openMetric('unique_customers')"
          >
            <span class="absolute top-3.5 right-3.5 text-slate-300 group-hover:text-slate-500 transition-colors" aria-hidden="true">
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="9" />
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
              </svg>
            </span>
            <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.uniqueCustomers') }}</p>
            <p class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight tabular-nums">
              {{ formatCount(data.unique_customers) }}
            </p>
            <p class="mt-2 text-sm text-slate-500">{{ t('dashboard.subline.inPeriod') }}</p>
          </button>
        </div>

        <!-- Trend + forecast -->
        <div class="bg-white rounded-xl border border-slate-200 p-6 mb-5 md:mb-6">
          <div class="flex items-baseline justify-between mb-4 gap-3 flex-wrap">
            <div>
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">
                {{ t('dashboard.trend.title') }}
              </h2>
              <p class="mt-0.5 text-sm text-slate-500">
                {{ t('dashboard.trend.subtitle') }}
              </p>
            </div>
            <div class="inline-flex items-center gap-4 text-sm">
              <button
                type="button"
                class="group text-left rounded-md px-2 py-1 -mx-2 -my-1 cursor-pointer hover:bg-slate-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70"
                @click="openMetric('forecast_bookings')"
              >
                <p class="text-slate-500 inline-flex items-center gap-1">
                  {{ t('dashboard.metrics.forecastBookings') }}
                  <svg
                    class="h-3.5 w-3.5 text-slate-300 group-hover:text-slate-500 transition-colors"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="12" r="9" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
                  </svg>
                </p>
                <p class="font-semibold text-slate-900 tabular-nums">
                  {{ Math.round(forecastTotal.bookings) }}
                </p>
              </button>
              <button
                type="button"
                class="group text-left rounded-md px-2 py-1 -mx-2 -my-1 cursor-pointer hover:bg-slate-50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70"
                @click="openMetric('forecast_revenue')"
              >
                <p class="text-slate-500 inline-flex items-center gap-1">
                  {{ t('dashboard.metrics.forecastRevenue') }}
                  <svg
                    class="h-3.5 w-3.5 text-slate-300 group-hover:text-slate-500 transition-colors"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="1.8"
                    viewBox="0 0 24 24"
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="12" r="9" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M12 11v5m0-8h.01" />
                  </svg>
                </p>
                <p class="font-semibold text-slate-900 tabular-nums">
                  {{ formatPrice(forecastTotal.revenue) }}
                </p>
              </button>
            </div>
          </div>
          <div v-if="data.series.length > 0" style="height: 300px">
            <Line :data="trendChartData" :options="trendChartOptions" />
          </div>
          <div v-else class="h-52 flex items-center justify-center text-sm text-slate-400">
            No booking data for this period.
          </div>
        </div>

        <!-- Day of week + peak hours -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 md:gap-6 mb-5 md:mb-6">
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">{{ t('dashboard.busiestDays') }}</h2>
              <p class="mt-0.5 text-sm text-slate-500">{{ t('dashboard.busiestDaysSubtitle') }}</p>
            </div>
            <div style="height: 240px">
              <Bar :data="dowChartData" :options="dowChartOptions" />
            </div>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">{{ t('dashboard.peakHours') }}</h2>
              <p class="mt-0.5 text-sm text-slate-500">{{ t('dashboard.peakHoursSubtitle') }}</p>
            </div>
            <div class="space-y-1.5">
              <div
                v-for="h in peakHours.rows.filter((r) => r.count > 0)"
                :key="h.hour"
                class="flex items-center gap-3 text-sm"
              >
                <span class="w-14 tabular-nums text-slate-500">{{ formatHour(h.hour) }}</span>
                <div class="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-slate-900 rounded-full transition-all duration-300"
                    :style="{ width: peakHours.max > 0 ? `${(h.count / peakHours.max) * 100}%` : '0%' }"
                  />
                </div>
                <span class="w-10 text-right tabular-nums font-medium text-slate-900">{{ h.count }}</span>
              </div>
              <p v-if="peakHours.rows.every((r) => r.count === 0)" class="text-sm text-slate-400 text-center py-6">
                No bookings yet for this period.
              </p>
            </div>
          </div>
        </div>

        <!-- Top services + Outcome breakdown -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 md:gap-6 mb-5 md:mb-6">
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">{{ t('dashboard.topServices') }}</h2>
              <p class="mt-0.5 text-sm text-slate-500">{{ t('dashboard.topServicesSubtitle') }}</p>
            </div>
            <ul class="space-y-3">
              <li
                v-for="svc in topServices"
                :key="svc.name"
                class="flex items-center gap-3"
              >
                <div class="flex-1 min-w-0">
                  <div class="flex items-baseline justify-between gap-2 mb-1">
                    <span class="text-sm font-medium text-slate-900 truncate">{{ svc.name }}</span>
                    <span class="text-sm text-slate-500 tabular-nums">
                      {{ svc.count }} · {{ formatPrice(svc.revenue) }}
                    </span>
                  </div>
                  <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      class="h-full bg-slate-900 rounded-full transition-all duration-300"
                      :style="{ width: maxServiceCount > 0 ? `${(svc.count / maxServiceCount) * 100}%` : '0%' }"
                    />
                  </div>
                </div>
              </li>
              <li v-if="topServices.length === 0" class="text-sm text-slate-400 text-center py-6">
                No services delivered yet.
              </li>
            </ul>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">{{ t('dashboard.outcomesTitle') }}</h2>
              <p class="mt-0.5 text-sm text-slate-500">
                {{ t('dashboard.outcomesSubtitle') }}
              </p>
            </div>
            <ul class="space-y-3">
              <li class="flex items-center gap-3">
                <span class="h-2 w-2 rounded-full bg-emerald-500 flex-shrink-0"></span>
                <span class="text-sm text-slate-700 flex-1">{{ t('dashboard.outcomeCompleted') }}</span>
                <span class="text-sm tabular-nums text-slate-500">{{ statusPct(data.status_breakdown.completed) }}</span>
                <span class="text-sm font-semibold text-slate-900 tabular-nums w-8 text-right">
                  {{ data.status_breakdown.completed }}
                </span>
              </li>
              <li class="flex items-center gap-3">
                <span class="h-2 w-2 rounded-full bg-slate-400 flex-shrink-0"></span>
                <span class="text-sm text-slate-700 flex-1">{{ t('dashboard.outcomeUpcoming') }}</span>
                <span class="text-sm tabular-nums text-slate-500">{{ statusPct(data.status_breakdown.confirmed) }}</span>
                <span class="text-sm font-semibold text-slate-900 tabular-nums w-8 text-right">
                  {{ data.status_breakdown.confirmed }}
                </span>
              </li>
              <li class="flex items-center gap-3">
                <span class="h-2 w-2 rounded-full bg-slate-300 flex-shrink-0"></span>
                <span class="text-sm text-slate-700 flex-1">{{ t('dashboard.outcomeCancelled') }}</span>
                <span class="text-sm tabular-nums text-slate-500">{{ statusPct(data.status_breakdown.cancelled) }}</span>
                <span class="text-sm font-semibold text-slate-900 tabular-nums w-8 text-right">
                  {{ data.status_breakdown.cancelled }}
                </span>
              </li>
              <li class="flex items-center gap-3">
                <span class="h-2 w-2 rounded-full bg-red-500 flex-shrink-0"></span>
                <span class="text-sm text-slate-700 flex-1">{{ t('dashboard.outcomeNoShow') }}</span>
                <span class="text-sm tabular-nums text-slate-500">{{ statusPct(data.status_breakdown.no_show) }}</span>
                <span class="text-sm font-semibold text-slate-900 tabular-nums w-8 text-right">
                  {{ data.status_breakdown.no_show }}
                </span>
              </li>
            </ul>
          </div>
        </div>

        <!-- Rating distribution + recent reviews -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 md:gap-6">
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">{{ t('dashboard.ratingDistribution') }}</h2>
              <p class="mt-0.5 text-sm text-slate-500">
                {{ t('dashboard.ratingDistributionSubtitle', { count: data.ratings.count }) }}
              </p>
            </div>
            <ul class="space-y-2">
              <li
                v-for="row in ratingDistRows"
                :key="row.star"
                class="flex items-center gap-3"
              >
                <span class="w-8 inline-flex items-center gap-1 text-sm font-medium text-slate-600 tabular-nums">
                  {{ row.star }}
                  <svg class="h-3.5 w-3.5 text-amber-400 fill-current" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                </span>
                <div class="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-amber-400 rounded-full transition-all duration-500"
                    :style="{ width: `${row.pct}%` }"
                  />
                </div>
                <span class="w-10 text-right text-sm text-slate-500 tabular-nums">{{ row.count }}</span>
              </li>
              <li v-if="data.ratings.count === 0" class="text-sm text-slate-400 text-center py-6">
                No reviews yet.
              </li>
            </ul>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">{{ t('dashboard.recentReviews') }}</h2>
              <p class="mt-0.5 text-sm text-slate-500">{{ t('dashboard.recentReviewsSubtitle', { count: data.ratings.recent.length }) }}</p>
            </div>
            <ul v-if="data.ratings.recent.length > 0" class="divide-y divide-slate-100">
              <li
                v-for="(review, idx) in data.ratings.recent"
                :key="idx"
                class="px-6 py-4"
              >
                <div class="flex items-center justify-between gap-3 mb-1.5">
                  <div class="flex items-center gap-2 min-w-0">
                    <span class="text-sm font-semibold text-slate-900 truncate">{{ review.reviewer }}</span>
                    <div class="flex items-center gap-0.5 flex-shrink-0">
                      <svg
                        v-for="star in 5"
                        :key="star"
                        class="h-3.5 w-3.5"
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
                <p v-else class="text-sm text-slate-400 italic">{{ t('dashboard.noWrittenReview') }}</p>
              </li>
            </ul>
            <div v-else class="px-6 py-10 text-center text-sm text-slate-400">
              Reviews will show up here as soon as customers leave them.
            </div>
          </div>
        </div>
      </template>
    </section>
  </BarberLayout>

  <BaseModal
    :open="!!activeMetricInfo && !!data"
    :eyebrow="activeMetricInfo?.eyebrow ?? periodLabel"
    :title="activeMetricInfo?.title"
    size="md"
    @close="closeMetric"
  >
    <template v-if="activeMetricInfo && data">
      <div class="px-5 md:px-6 py-5 border-b border-slate-200">
        <p class="text-4xl font-bold text-slate-900 tracking-tight tabular-nums">
          {{ activeMetricValueDisplay }}
        </p>
        <p class="mt-1.5 text-sm text-slate-500">{{ activeMetricSublineDisplay }}</p>
      </div>

      <div class="px-5 md:px-6 py-5 space-y-5">
        <section>
          <h3 class="text-sm font-semibold text-slate-900 tracking-tight mb-1.5">
            What this is
          </h3>
          <p class="text-sm text-slate-700 leading-relaxed">{{ activeMetricInfo.what }}</p>
        </section>
        <section>
          <h3 class="text-sm font-semibold text-slate-900 tracking-tight mb-1.5">
            How it's calculated
          </h3>
          <ul class="text-sm text-slate-700 leading-relaxed list-disc list-outside pl-5 space-y-1">
            <li v-for="(line, i) in activeMetricInfo.howLines" :key="i">{{ line }}</li>
          </ul>
        </section>
        <section>
          <h3 class="text-sm font-semibold text-slate-900 tracking-tight mb-1.5">
            Why it matters
          </h3>
          <p class="text-sm text-slate-700 leading-relaxed">{{ activeMetricInfo.why }}</p>
        </section>
      </div>
    </template>

    <template #footer>
      <div class="flex justify-end">
        <button
          type="button"
          class="inline-flex items-center justify-center h-10 px-4 rounded-md bg-slate-900 text-white text-sm font-medium hover:bg-slate-800 transition-colors"
          @click="closeMetric"
        >
          Got it
        </button>
      </div>
    </template>
  </BaseModal>
</template>
