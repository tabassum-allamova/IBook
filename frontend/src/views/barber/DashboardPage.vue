<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
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

interface AnalyticsData {
  total_bookings: number
  total_revenue: number
  trend: { day: string; count: number; revenue: number }[]
  top_services: { service_name: string; count: number }[]
  ratings_summary: { avg: number | null; count: number }
}

const periods = [
  { label: '7 days', value: '7d' },
  { label: '30 days', value: '30d' },
  { label: '90 days', value: '90d' },
  { label: 'All time', value: 'all' },
]

const period = ref('30d')

const { data: analyticsData, isLoading } = useQuery<AnalyticsData>({
  queryKey: computed(() => ['barber-analytics', period.value]),
  queryFn: () =>
    api
      .get<AnalyticsData>('/api/bookings/analytics/barber/', {
        params: { period: period.value },
      })
      .then((r) => r.data),
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

const topServicesChartData = computed(() => {
  const services = analyticsData.value?.top_services ?? []
  return {
    labels: services.map((s) => s.service_name),
    datasets: [
      {
        label: 'Bookings',
        data: services.map((s) => s.count),
        backgroundColor: '#C8A97C',
        borderRadius: 4,
      },
    ],
  }
})

const topServicesChartOptions = {
  indexAxis: 'y' as const,
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
  },
  scales: {
    x: {
      beginAtZero: true,
      ticks: { precision: 0 },
      grid: { color: 'rgba(0,0,0,0.04)' },
    },
    y: {
      grid: { display: false },
    },
  },
}
</script>

<template>
  <BarberLayout>
    <div class="p-6 lg:p-8">
      <!-- Page header -->
      <div class="mb-6">
        <h1 class="text-3xl font-bold text-ibook-brown-900">Analytics</h1>
        <p class="mt-1 text-sm text-ibook-brown-500">Track your performance</p>
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
        <div class="grid grid-cols-2 lg:grid-cols-3 gap-4">
          <div
            v-for="i in 3"
            :key="i"
            class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5 h-24"
          >
            <div class="h-3 bg-ibook-brown-100 rounded w-1/2 mb-3"></div>
            <div class="h-8 bg-ibook-brown-100 rounded w-1/3"></div>
          </div>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div
            v-for="i in 2"
            :key="i"
            class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5 h-72"
          >
            <div class="h-3 bg-ibook-brown-100 rounded w-1/3 mb-4"></div>
            <div class="h-52 bg-ibook-brown-50 rounded"></div>
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
            Analytics will appear when you complete appointments.
          </p>
        </div>

        <!-- Stat cards -->
        <div class="grid grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
          <!-- Total Bookings -->
          <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
            <p class="text-sm font-medium text-ibook-brown-500 mb-1">Total Bookings</p>
            <p class="text-3xl font-bold text-ibook-brown-900">
              {{ analyticsData.total_bookings }}
            </p>
          </div>

          <!-- Revenue -->
          <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
            <p class="text-sm font-medium text-ibook-brown-500 mb-1">Revenue</p>
            <p class="text-3xl font-bold text-ibook-gold-500">
              {{ formatPrice(analyticsData.total_revenue) }}
            </p>
          </div>

          <!-- Avg Rating -->
          <div
            class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5 col-span-2 lg:col-span-1"
          >
            <p class="text-sm font-medium text-ibook-brown-500 mb-1">Avg. Rating</p>
            <div class="flex items-baseline gap-1.5">
              <p class="text-3xl font-bold text-ibook-brown-900">
                {{ analyticsData.ratings_summary.avg?.toFixed(1) ?? '—' }}
              </p>
              <svg
                v-if="analyticsData.ratings_summary.avg"
                xmlns="http://www.w3.org/2000/svg"
                class="h-5 w-5 text-ibook-gold-400 mb-0.5"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
                />
              </svg>
            </div>
            <p class="text-xs text-ibook-brown-400 mt-1">
              {{ analyticsData.ratings_summary.count }} reviews
            </p>
          </div>
        </div>

        <!-- Charts -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <!-- Bookings Trend -->
          <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
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

          <!-- Top Services -->
          <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
            <h2 class="text-sm font-semibold text-ibook-brown-700 mb-4">Top Services</h2>
            <div v-if="analyticsData.top_services.length > 0" style="height: 250px">
              <Bar :data="topServicesChartData" :options="topServicesChartOptions" />
            </div>
            <div
              v-else
              class="h-48 flex items-center justify-center text-sm text-ibook-brown-400"
            >
              No service data
            </div>
          </div>
        </div>
      </template>
    </div>
  </BarberLayout>
</template>
