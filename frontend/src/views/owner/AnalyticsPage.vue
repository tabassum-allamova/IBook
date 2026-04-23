<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useQuery } from '@tanstack/vue-query'
import { Line, Bar } from 'vue-chartjs'

const { t } = useI18n()
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
import OwnerLayout from '@/layouts/OwnerLayout.vue'
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
interface BarberRow {
  id: number
  name: string
  bookings: number
  revenue: number
}

interface Analytics {
  total_bookings: number
  total_revenue: number
  avg_ticket: number
  previous: { total_bookings: number; total_revenue: number }
  series: SeriesPoint[]
  forecast: SeriesPoint[]
  top_services: ServiceRow[]
  day_of_week: DowRow[]
  hour_of_day: HodRow[]
  barbers: BarberRow[]
}

const periods = [
  { label: '7 days', value: '7d' },
  { label: '30 days', value: '30d' },
  { label: '90 days', value: '90d' },
]
const period = ref('30d')

const { data, isLoading } = useQuery<Analytics>({
  queryKey: computed(() => ['owner-analytics-full', period.value]),
  queryFn: () =>
    api
      .get<Analytics>('/api/bookings/analytics/owner/', { params: { period: period.value } })
      .then((r) => r.data),
})

// ---- Formatting helpers ----
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

const bookingsDelta = computed(() => {
  if (!data.value) return null
  return pctChange(data.value.total_bookings, data.value.previous.total_bookings)
})
const revenueDelta = computed(() => {
  if (!data.value) return null
  return pctChange(data.value.total_revenue, data.value.previous.total_revenue)
})

// ---- Trend + forecast chart ----
const trendChartData = computed(() => {
  if (!data.value) return { labels: [], datasets: [] }
  const history = data.value.series ?? []
  const forecast = data.value.forecast ?? []
  const labels = [...history.map((d) => formatDate(d.day)), ...forecast.map((d) => formatDate(d.day))]

  // History line — full length, then nulls for forecast days
  const histData: (number | null)[] = history.map((d) => d.count)
  histData.push(...forecast.map(() => null))

  // Forecast line — nulls for history, forecast values. Prepend last history point so the dashed line connects.
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
const DAY_NAMES = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
const dowChartData = computed(() => {
  const rows = data.value?.day_of_week ?? []
  return {
    labels: DAY_NAMES,
    datasets: [
      {
        label: 'Bookings',
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

function formatHour(h: number): string {
  if (h === 0) return '12 AM'
  if (h === 12) return '12 PM'
  return h < 12 ? `${h} AM` : `${h - 12} PM`
}

// ---- Forecast summary ----
const forecastTotal = computed(() => {
  if (!data.value?.forecast) return { bookings: 0, revenue: 0 }
  return data.value.forecast.reduce(
    (acc, r) => ({ bookings: acc.bookings + r.count, revenue: acc.revenue + r.revenue }),
    { bookings: 0, revenue: 0 },
  )
})

const topServices = computed(() => data.value?.top_services ?? [])
const maxServiceCount = computed(() =>
  topServices.value.reduce((m, s) => (s.count > m ? s.count : m), 0),
)

const sortedBarbers = computed(() =>
  [...(data.value?.barbers ?? [])].sort((a, b) => b.revenue - a.revenue),
)
</script>

<template>
  <OwnerLayout>
    <section class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
            {{ t('owner.analytics.title') }}
          </h1>
          <p class="mt-1 text-sm text-slate-600">
            {{ t('owner.analytics.subtitle') }}
          </p>
        </div>

        <!-- Period picker -->
        <div
          role="tablist"
          aria-label="Period"
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
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-5">
          <div v-for="i in 3" :key="i" class="bg-white rounded-xl border border-slate-200 p-6">
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
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 md:gap-5 mb-5 md:mb-6">
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <p class="text-sm font-medium text-slate-500 mb-2">Total bookings</p>
            <p class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight tabular-nums">
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
              <span class="text-slate-500"> vs. previous period</span>
            </p>
            <p v-else class="mt-2 text-sm text-slate-500">No prior data</p>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <p class="text-sm font-medium text-slate-500 mb-2">Total revenue</p>
            <p class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight tabular-nums">
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
              <span class="text-slate-500"> vs. previous period</span>
            </p>
            <p v-else class="mt-2 text-sm text-slate-500">No prior data</p>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <p class="text-sm font-medium text-slate-500 mb-2">Average ticket</p>
            <p class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight tabular-nums">
              {{ formatPrice(data.avg_ticket) }}
            </p>
            <p class="mt-2 text-sm text-slate-500">
              Across {{ formatCount(data.total_bookings) }}
              {{ data.total_bookings === 1 ? 'appointment' : 'appointments' }}
            </p>
          </div>
        </div>

        <!-- Trend + forecast -->
        <div class="bg-white rounded-xl border border-slate-200 p-6 mb-5 md:mb-6">
          <div class="flex items-baseline justify-between mb-4 gap-3 flex-wrap">
            <div>
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">
                Bookings trend &amp; 7-day forecast
              </h2>
              <p class="mt-0.5 text-sm text-slate-500">
                Dashed line projects the next 7 days based on recent trend.
              </p>
            </div>
            <div class="inline-flex items-center gap-4 text-sm">
              <div>
                <p class="text-slate-500">Projected bookings (next 7 days)</p>
                <p class="font-semibold text-slate-900 tabular-nums">
                  {{ Math.round(forecastTotal.bookings) }}
                </p>
              </div>
              <div>
                <p class="text-slate-500">Projected revenue</p>
                <p class="font-semibold text-slate-900 tabular-nums">
                  {{ formatPrice(forecastTotal.revenue) }}
                </p>
              </div>
            </div>
          </div>
          <div v-if="data.series.length > 0" style="height: 300px">
            <Line :data="trendChartData" :options="trendChartOptions" />
          </div>
          <div v-else class="h-52 flex items-center justify-center text-sm text-slate-400">
            No booking data for this period.
          </div>
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 md:gap-6 mb-5 md:mb-6">
          <!-- Day of week -->
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">
                Busiest days
              </h2>
              <p class="mt-0.5 text-sm text-slate-500">Bookings by weekday.</p>
            </div>
            <div style="height: 240px">
              <Bar :data="dowChartData" :options="dowChartOptions" />
            </div>
          </div>

          <!-- Peak hours -->
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">
                Peak hours
              </h2>
              <p class="mt-0.5 text-sm text-slate-500">Share of bookings per hour of day.</p>
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

        <!-- Top services + Barber ranking -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-5 md:gap-6">
          <!-- Top services -->
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">
                Top services
              </h2>
              <p class="mt-0.5 text-sm text-slate-500">By bookings in this period.</p>
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
                No services sold yet.
              </li>
            </ul>
          </div>

          <!-- Barber ranking -->
          <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">
                Barber performance
              </h2>
              <p class="mt-0.5 text-sm text-slate-500">Sorted by revenue.</p>
            </div>
            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 bg-slate-50/50">
                    <th class="text-left py-3 px-6 font-medium text-slate-500">Barber</th>
                    <th class="text-right py-3 px-6 font-medium text-slate-500">Bookings</th>
                    <th class="text-right py-3 px-6 font-medium text-slate-500">Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="sortedBarbers.length === 0">
                    <td colspan="3" class="py-10 text-center text-sm text-slate-400">
                      No barber data for this period.
                    </td>
                  </tr>
                  <tr
                    v-for="b in sortedBarbers"
                    :key="b.id"
                    class="border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors"
                  >
                    <td class="py-3 px-6">
                      <span class="font-medium text-slate-900">{{ b.name }}</span>
                    </td>
                    <td class="py-3 px-6 text-right text-slate-700 tabular-nums">
                      {{ formatCount(b.bookings) }}
                    </td>
                    <td class="py-3 px-6 text-right font-medium text-slate-900 tabular-nums">
                      {{ formatPrice(b.revenue) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </template>
    </section>
  </OwnerLayout>
</template>
