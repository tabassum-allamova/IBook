<script setup lang="ts">
import { ref, computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { useQuery } from '@tanstack/vue-query'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
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
  Title,
  Tooltip,
  Legend,
  Filler,
)

interface OwnerAnalyticsData {
  total_bookings: number
  total_revenue: number
  trend: { day: string; count: number; revenue: number }[]
  barbers: { id: number; name: string; bookings: number; revenue: number }[]
}

const { t } = useI18n()

const periods = computed(() => [
  { label: t('dashboard.periods.7d'), value: '7d' },
  { label: t('dashboard.periods.30d'), value: '30d' },
  { label: t('dashboard.periods.90d'), value: '90d' },
  { label: t('dashboard.periods.all'), value: 'all' },
])

const period = ref('30d')
const sortKey = ref<'name' | 'bookings' | 'revenue'>('bookings')
const sortDir = ref<'asc' | 'desc'>('desc')

const { data: analyticsData, isLoading } = useQuery<OwnerAnalyticsData>({
  queryKey: computed(() => ['owner-analytics', period.value]),
  queryFn: () =>
    api
      .get<OwnerAnalyticsData>('/api/bookings/analytics/owner/', {
        params: { period: period.value },
      })
      .then((r) => r.data),
})

function toggleSort(key: 'name' | 'bookings' | 'revenue') {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortKey.value = key
    sortDir.value = 'desc'
  }
}

const sortedBarbers = computed(() => {
  const barbers = [...(analyticsData.value?.barbers ?? [])]
  return barbers.sort((a, b) => {
    const dir = sortDir.value === 'asc' ? 1 : -1
    if (sortKey.value === 'name') {
      return dir * a.name.localeCompare(b.name)
    }
    return dir * (a[sortKey.value] - b[sortKey.value])
  })
})

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

function formatPrice(n: number): string {
  return new Intl.NumberFormat('en-US').format(n) + ' UZS'
}

function formatCount(n: number): string {
  return new Intl.NumberFormat('en-US').format(n)
}

const trendChartData = computed(() => {
  const trend = analyticsData.value?.trend ?? []
  return {
    labels: trend.map((d) => formatDate(d.day)),
    datasets: [
      {
        label: 'Bookings',
        data: trend.map((d) => d.count),
        borderColor: '#0f172a',
        backgroundColor: 'rgba(15, 23, 42, 0.06)',
        tension: 0.35,
        fill: true,
        pointBackgroundColor: '#0f172a',
        pointBorderColor: '#fff',
        pointBorderWidth: 2,
        pointRadius: 3,
        pointHoverRadius: 5,
      },
    ],
  }
})

const trendChartOptions = {
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
      ticks: { color: '#94a3b8', font: { size: 12 } },
      border: { display: false },
    },
  },
}

</script>

<template>
  <OwnerLayout>
    <section class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
            {{ t('owner.overview.title') }}
          </h1>
          <p class="mt-1 text-sm text-slate-600">
            {{ t('owner.overview.subtitle') }}
          </p>
        </div>

        <!-- Period segmented control -->
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

      <!-- Loading skeleton -->
      <div v-if="isLoading" class="space-y-5">
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5">
          <div
            v-for="i in 2"
            :key="i"
            class="bg-white rounded-xl border border-slate-200 p-6"
          >
            <div class="h-4 bg-slate-100 animate-pulse rounded w-1/3 mb-3" />
            <div class="h-9 bg-slate-100 animate-pulse rounded w-1/2" />
          </div>
        </div>
        <div class="bg-white rounded-xl border border-slate-200 p-6">
          <div class="h-4 bg-slate-100 animate-pulse rounded w-1/4 mb-4" />
          <div class="h-64 bg-slate-100 animate-pulse rounded" />
        </div>
        <div class="bg-white rounded-xl border border-slate-200 p-6">
          <div class="h-4 bg-slate-100 animate-pulse rounded w-1/4 mb-4" />
          <div class="space-y-2.5">
            <div v-for="i in 4" :key="i" class="h-10 bg-slate-100 animate-pulse rounded" />
          </div>
        </div>
      </div>

      <!-- Content -->
      <template v-else-if="analyticsData">
        <!-- Empty state -->
        <div
          v-if="analyticsData.total_bookings === 0"
          class="bg-white rounded-xl border border-slate-200 p-12 flex flex-col items-center text-center"
        >
          <div class="w-12 h-12 rounded-lg bg-slate-100 flex items-center justify-center mb-4">
            <svg class="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-slate-900 tracking-tight mb-1">
            No data yet
          </h3>
          <p class="text-sm text-slate-500 max-w-xs leading-relaxed">
            Analytics will show up as soon as your barbers start taking appointments.
          </p>
        </div>

        <template v-else>
          <!-- Stat cards -->
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 md:gap-5 mb-5 md:mb-6">
            <div class="bg-white rounded-xl border border-slate-200 p-6">
              <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.totalBookings') }}</p>
              <p class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight tabular-nums">
                {{ formatCount(analyticsData.total_bookings) }}
              </p>
            </div>
            <div class="bg-white rounded-xl border border-slate-200 p-6">
              <p class="text-sm font-medium text-slate-500 mb-2">{{ t('dashboard.metrics.revenue') }}</p>
              <p class="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight tabular-nums">
                {{ formatPrice(analyticsData.total_revenue) }}
              </p>
            </div>
          </div>

          <!-- Trend chart -->
          <div class="bg-white rounded-xl border border-slate-200 p-6 mb-5 md:mb-6">
            <div class="flex items-baseline justify-between mb-4">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">
                {{ t('dashboard.trend.title') }}
              </h2>
              <p class="text-sm text-slate-500">Daily count</p>
            </div>
            <div v-if="analyticsData.trend.length > 0" style="height: 260px">
              <Line :data="trendChartData" :options="trendChartOptions" />
            </div>
            <div
              v-else
              class="h-52 flex items-center justify-center text-sm text-slate-400"
            >
              {{ t('dashboard.trend.empty') }}
            </div>
          </div>

          <!-- Barber ranking -->
          <div class="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div class="px-6 py-4 border-b border-slate-200 flex items-baseline justify-between">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">
                Barber performance
              </h2>
              <p class="text-sm text-slate-500">
                {{ sortedBarbers.length }} {{ sortedBarbers.length === 1 ? 'barber' : 'barbers' }}
              </p>
            </div>

            <div class="overflow-x-auto">
              <table class="w-full text-sm">
                <thead>
                  <tr class="border-b border-slate-200 bg-slate-50/50">
                    <th
                      class="text-left py-3 px-6 font-medium text-slate-500 select-none cursor-pointer hover:text-slate-900 transition-colors"
                      @click="toggleSort('name')"
                    >
                      <span class="inline-flex items-center gap-1">
                        Barber
                        <svg
                          v-if="sortKey === 'name'"
                          class="h-3.5 w-3.5 text-slate-700 transition-transform"
                          :class="sortDir === 'asc' ? 'rotate-180' : ''"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                      </span>
                    </th>
                    <th
                      class="text-right py-3 px-6 font-medium text-slate-500 select-none cursor-pointer hover:text-slate-900 transition-colors"
                      @click="toggleSort('bookings')"
                    >
                      <span class="inline-flex items-center justify-end gap-1 w-full">
                        Bookings
                        <svg
                          v-if="sortKey === 'bookings'"
                          class="h-3.5 w-3.5 text-slate-700 transition-transform"
                          :class="sortDir === 'asc' ? 'rotate-180' : ''"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                      </span>
                    </th>
                    <th
                      class="text-right py-3 px-6 font-medium text-slate-500 select-none cursor-pointer hover:text-slate-900 transition-colors"
                      @click="toggleSort('revenue')"
                    >
                      <span class="inline-flex items-center justify-end gap-1 w-full">
                        Revenue
                        <svg
                          v-if="sortKey === 'revenue'"
                          class="h-3.5 w-3.5 text-slate-700 transition-transform"
                          :class="sortDir === 'asc' ? 'rotate-180' : ''"
                          viewBox="0 0 20 20"
                          fill="currentColor"
                        >
                          <path fill-rule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clip-rule="evenodd" />
                        </svg>
                      </span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-if="sortedBarbers.length === 0">
                    <td colspan="3" class="py-12 text-center text-sm text-slate-400">
                      No barber data for this period.
                    </td>
                  </tr>
                  <tr
                    v-for="barber in sortedBarbers"
                    :key="barber.id"
                    class="border-b border-slate-100 last:border-0 hover:bg-slate-50/50 transition-colors"
                  >
                    <td class="py-3 px-6">
                      <span class="font-medium text-slate-900">{{ barber.name }}</span>
                    </td>
                    <td class="py-3 px-6 text-right text-slate-700 tabular-nums">
                      {{ formatCount(barber.bookings) }}
                    </td>
                    <td class="py-3 px-6 text-right font-medium text-slate-900 tabular-nums">
                      {{ formatPrice(barber.revenue) }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </template>
      </template>
    </section>
  </OwnerLayout>
</template>
