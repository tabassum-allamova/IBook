<script setup lang="ts">
import { ref, computed } from 'vue'
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
import { useAuthStore } from '@/stores/auth'
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

const auth = useAuthStore()

const periods = [
  { label: '7 days', value: '7d' },
  { label: '30 days', value: '30d' },
  { label: '90 days', value: '90d' },
  { label: 'All time', value: 'all' },
]

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

const trendChartData = computed(() => {
  const trend = analyticsData.value?.trend ?? []
  return {
    labels: trend.map((d) => formatDate(d.day)),
    datasets: [
      {
        label: 'Bookings',
        data: trend.map((d) => d.count),
        borderColor: '#6B4C2E',
        backgroundColor: 'rgba(107,76,46,0.08)',
        tension: 0.3,
        fill: true,
        pointBackgroundColor: '#6B4C2E',
        pointRadius: 3,
      },
    ],
  }
})

const trendChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: { precision: 0 },
      grid: { color: 'rgba(0,0,0,0.04)' },
    },
    x: {
      grid: { display: false },
    },
  },
}
</script>

<template>
  <OwnerLayout>
    <div class="p-4 md:p-6 lg:p-8">
      <!-- Page header -->
      <div class="mb-6">
        <h1 class="text-xl md:text-3xl font-bold text-ibook-brown-900">Shop Overview</h1>
        <p class="mt-1 text-sm text-ibook-brown-500">
          Welcome back, {{ auth.user?.fullName }}. Here's how your shop is performing.
        </p>
      </div>

      <!-- Period filter -->
      <div class="flex flex-wrap gap-2 mb-6">
        <button
          v-for="p in periods"
          :key="p.value"
          @click="period = p.value"
          class="rounded-lg text-sm font-medium px-3 py-1.5 transition-colors"
          :class="
            period === p.value
              ? 'bg-ibook-brown-800 text-white'
              : 'bg-white text-ibook-brown-600 border border-ibook-brown-200 hover:bg-ibook-brown-50'
          "
        >
          {{ p.label }}
        </button>
      </div>

      <!-- Loading skeleton -->
      <div v-if="isLoading" class="animate-pulse space-y-4">
        <div class="grid grid-cols-2 gap-4">
          <div
            v-for="i in 2"
            :key="i"
            class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5 h-24"
          >
            <div class="h-3 bg-ibook-brown-100 rounded w-1/2 mb-3"></div>
            <div class="h-8 bg-ibook-brown-100 rounded w-1/3"></div>
          </div>
        </div>
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5 h-72">
          <div class="h-3 bg-ibook-brown-100 rounded w-1/4 mb-4"></div>
          <div class="h-52 bg-ibook-brown-50 rounded"></div>
        </div>
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <div class="h-3 bg-ibook-brown-100 rounded w-1/4 mb-4"></div>
          <div class="space-y-3">
            <div v-for="i in 4" :key="i" class="h-10 bg-ibook-brown-50 rounded"></div>
          </div>
        </div>
      </div>

      <!-- Content -->
      <template v-else-if="analyticsData">
        <!-- Empty state -->
        <div
          v-if="analyticsData.total_bookings === 0"
          class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-12 flex flex-col items-center text-center mb-6"
        >
          <div
            class="w-14 h-14 rounded-full bg-ibook-brown-100 flex items-center justify-center mb-4"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-7 w-7 text-ibook-brown-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h3 class="text-base font-semibold text-ibook-brown-800 mb-1">No data yet</h3>
          <p class="text-ibook-brown-500 text-sm max-w-xs">
            Analytics will appear when barbers complete appointments.
          </p>
        </div>

        <!-- Stat cards -->
        <div class="grid grid-cols-2 gap-4 mb-6">
          <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
            <p class="text-sm font-medium text-ibook-brown-500 mb-1">Total Bookings</p>
            <p class="text-3xl font-bold text-ibook-brown-900">
              {{ analyticsData.total_bookings }}
            </p>
          </div>
          <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
            <p class="text-sm font-medium text-ibook-brown-500 mb-1">Total Revenue</p>
            <p class="text-3xl font-bold text-ibook-gold-500">
              {{ formatPrice(analyticsData.total_revenue) }}
            </p>
          </div>
        </div>

        <!-- Trend chart -->
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5 mb-6">
          <h2 class="text-sm font-semibold text-ibook-brown-700 mb-4">Bookings Trend</h2>
          <div v-if="analyticsData.trend.length > 0" style="height: 250px">
            <Line :data="trendChartData" :options="trendChartOptions" />
          </div>
          <div
            v-else
            class="h-48 flex items-center justify-center text-sm text-ibook-brown-400"
          >
            No booking data for this period
          </div>
        </div>

        <!-- Barber ranking table -->
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm overflow-hidden">
          <div class="px-6 py-4 border-b border-ibook-brown-100">
            <h2 class="text-sm font-semibold text-ibook-brown-700">Barber Performance</h2>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-ibook-brown-100">
                  <th
                    class="text-left py-3 px-4 text-xs font-medium text-ibook-brown-500 uppercase tracking-wide cursor-pointer hover:text-ibook-brown-800 select-none"
                    @click="toggleSort('name')"
                  >
                    <span class="flex items-center gap-1">
                      Barber Name
                      <svg
                        v-if="sortKey === 'name'"
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3.5 w-3.5 text-ibook-brown-700 transition-transform"
                        :class="sortDir === 'asc' ? 'rotate-180' : ''"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                          clip-rule="evenodd"
                        />
                      </svg>
                      <svg
                        v-else
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3.5 w-3.5 text-ibook-brown-300"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3zm-3.707 9.293a1 1 0 000 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L10 14.586l-2.293-2.293a1 1 0 00-1.414 0z"
                          clip-rule="evenodd"
                        />
                      </svg>
                    </span>
                  </th>
                  <th
                    class="text-center py-3 px-4 text-xs font-medium text-ibook-brown-500 uppercase tracking-wide cursor-pointer hover:text-ibook-brown-800 select-none"
                    @click="toggleSort('bookings')"
                  >
                    <span class="flex items-center justify-center gap-1">
                      Bookings
                      <svg
                        v-if="sortKey === 'bookings'"
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3.5 w-3.5 text-ibook-brown-700 transition-transform"
                        :class="sortDir === 'asc' ? 'rotate-180' : ''"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                          clip-rule="evenodd"
                        />
                      </svg>
                      <svg
                        v-else
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3.5 w-3.5 text-ibook-brown-300"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3zm-3.707 9.293a1 1 0 000 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L10 14.586l-2.293-2.293a1 1 0 00-1.414 0z"
                          clip-rule="evenodd"
                        />
                      </svg>
                    </span>
                  </th>
                  <th
                    class="text-right py-3 px-4 text-xs font-medium text-ibook-brown-500 uppercase tracking-wide cursor-pointer hover:text-ibook-brown-800 select-none"
                    @click="toggleSort('revenue')"
                  >
                    <span class="flex items-center justify-end gap-1">
                      Revenue (UZS)
                      <svg
                        v-if="sortKey === 'revenue'"
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3.5 w-3.5 text-ibook-brown-700 transition-transform"
                        :class="sortDir === 'asc' ? 'rotate-180' : ''"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
                          clip-rule="evenodd"
                        />
                      </svg>
                      <svg
                        v-else
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-3.5 w-3.5 text-ibook-brown-300"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                      >
                        <path
                          fill-rule="evenodd"
                          d="M10 3a1 1 0 01.707.293l3 3a1 1 0 01-1.414 1.414L10 5.414 7.707 7.707a1 1 0 01-1.414-1.414l3-3A1 1 0 0110 3zm-3.707 9.293a1 1 0 000 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L10 14.586l-2.293-2.293a1 1 0 00-1.414 0z"
                          clip-rule="evenodd"
                        />
                      </svg>
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-if="sortedBarbers.length === 0"
                  class="text-center"
                >
                  <td colspan="3" class="py-10 text-ibook-brown-400 text-sm">
                    No barber data
                  </td>
                </tr>
                <tr
                  v-for="(barber, index) in sortedBarbers"
                  :key="barber.id"
                  class="border-b border-ibook-brown-100 last:border-0"
                  :class="index % 2 === 1 ? 'bg-ibook-brown-50/30' : ''"
                >
                  <td class="py-3 px-4 font-medium text-ibook-brown-900">{{ barber.name }}</td>
                  <td class="py-3 px-4 text-center text-ibook-brown-700">{{ barber.bookings }}</td>
                  <td class="py-3 px-4 text-right text-ibook-brown-700">
                    {{ formatPrice(barber.revenue) }}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </template>
    </div>
  </OwnerLayout>
</template>
