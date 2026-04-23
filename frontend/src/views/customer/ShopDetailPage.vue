<script setup lang="ts">
import { computed, ref, markRaw, watch, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useQuery } from '@tanstack/vue-query'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Vite icon fix — idempotent, safe to repeat
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
;(globalThis as unknown as Record<string, unknown>).L = L
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

import { LMap, LTileLayer, LMarker } from '@vue-leaflet/vue-leaflet'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import BarberCard from '@/components/discovery/BarberCard.vue'
import api from '@/lib/axios'

const props = defineProps<{
  shopId: string
}>()

const { t } = useI18n()
const shopIdNum = computed(() => Number(props.shopId))

interface HoursEntry {
  id: number
  day_of_week: number
  is_open: boolean
  opens_at: string | null
  closes_at: string | null
  break_start: string | null
  break_end: string | null
}

interface ShopPhoto {
  id: number
  image: string
  uploaded_at: string
}

interface TopService {
  id: number
  name: string
  price: number
}

interface BarberMemberEntry {
  id: number
  barber: {
    id: number
    full_name: string
    email: string
    avatar: string | null
    top_services: TopService[]
  }
  added_at: string
}

interface ShopDetail {
  id: number
  name: string
  address: string
  lat: number | null
  lng: number | null
  description: string
  hours: HoursEntry[]
  photos: ShopPhoto[]
  members: BarberMemberEntry[]
  created_at: string
}

const { data: shop, isLoading, isError } = useQuery({
  queryKey: computed(() => ['shop', shopIdNum.value]),
  queryFn: async () => {
    const res = await api.get<ShopDetail>(`/api/shops/${shopIdNum.value}/`)
    return res.data
  },
  enabled: computed(() => !isNaN(shopIdNum.value)),
  retry: (failureCount, error: unknown) => {
    const axiosError = error as { response?: { status: number } }
    if (axiosError?.response?.status === 404) return false
    return failureCount < 2
  },
})

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const todayIndex = computed(() => {
  const jsDay = new Date().getDay()
  return (jsDay + 6) % 7
})

function formatTime(t: string | null): string {
  if (!t) return ''
  return t.slice(0, 5)
}

function getHoursForDay(dayIndex: number): HoursEntry | undefined {
  return shop.value?.hours.find((h) => h.day_of_week === dayIndex)
}

// markRaw prevents Leaflet from recursing on a Vue Proxy (extend → toLatLngBounds loop)
const mapCenter = computed<[number, number] | null>(() => {
  if (shop.value?.lat && shop.value?.lng) {
    return markRaw<[number, number]>([Number(shop.value.lat), Number(shop.value.lng)])
  }
  return null
})

const todaysHours = computed(() => getHoursForDay(todayIndex.value))

const isOpenNow = computed(() => {
  const h = todaysHours.value
  if (!h || !h.is_open || !h.opens_at || !h.closes_at) return false
  const now = new Date()
  const current = now.getHours() * 60 + now.getMinutes()
  const [oh, om] = h.opens_at.split(':').map(Number)
  const [ch, cm] = h.closes_at.split(':').map(Number)
  const open = oh * 60 + om
  const close = ch * 60 + cm
  if (current < open || current >= close) return false
  if (h.break_start && h.break_end) {
    const [bsh, bsm] = h.break_start.split(':').map(Number)
    const [beh, bem] = h.break_end.split(':').map(Number)
    if (current >= bsh * 60 + bsm && current < beh * 60 + bem) return false
  }
  return true
})

const todaysHoursLabel = computed(() => {
  const h = todaysHours.value
  if (!h || !h.is_open || !h.opens_at || !h.closes_at) return 'Closed today'
  return `Today · ${formatTime(h.opens_at)} – ${formatTime(h.closes_at)}`
})

function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-US').format(amount) + ' UZS'
}

// Shop initials for the avatar tile
const shopInitials = computed(() => {
  if (!shop.value) return ''
  return shop.value.name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join('')
    .toUpperCase()
})

const primaryPhoto = computed(() => shop.value?.photos?.[0] ?? null)

// Aggregate services across all barbers: name → min/max price + barbers offering it
interface AggregatedService {
  name: string
  minPrice: number
  maxPrice: number
  barberCount: number
}

const aggregatedServices = computed<AggregatedService[]>(() => {
  if (!shop.value) return []
  const map = new Map<string, { min: number; max: number; barbers: Set<number> }>()
  shop.value.members.forEach((m) => {
    m.barber.top_services.forEach((s) => {
      const existing = map.get(s.name)
      if (existing) {
        existing.min = Math.min(existing.min, s.price)
        existing.max = Math.max(existing.max, s.price)
        existing.barbers.add(m.barber.id)
      } else {
        map.set(s.name, { min: s.price, max: s.price, barbers: new Set([m.barber.id]) })
      }
    })
  })
  return Array.from(map.entries())
    .map(([name, v]) => ({
      name,
      minPrice: v.min,
      maxPrice: v.max,
      barberCount: v.barbers.size,
    }))
    .sort((a, b) => a.minPrice - b.minPrice)
})

// Tabs
type Tab = 'services' | 'team' | 'photos'
const activeTab = ref<Tab>('services')

// ---- Booking modal ----
const isBookOpen = ref(false)
const bookingServiceName = ref<string | null>(null)

const bookingMembers = computed(() => {
  if (!shop.value) return []
  if (!bookingServiceName.value) return shop.value.members
  return shop.value.members.filter((m) =>
    m.barber.top_services.some((s) => s.name === bookingServiceName.value),
  )
})

function openBooking() {
  bookingServiceName.value = null
  isBookOpen.value = true
}

function openBookingForService(name: string) {
  bookingServiceName.value = name
  isBookOpen.value = true
}

function closeBooking() {
  isBookOpen.value = false
  bookingServiceName.value = null
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isBookOpen.value) closeBooking()
}

watch(isBookOpen, (open) => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = open ? 'hidden' : ''
  if (open) {
    window.addEventListener('keydown', onKeydown)
  } else {
    window.removeEventListener('keydown', onKeydown)
  }
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (typeof document !== 'undefined') {
    document.body.style.overflow = ''
  }
})

function barberMinPrice(services: TopService[]): number | null {
  if (!services.length) return null
  return services.reduce((m, s) => (s.price < m ? s.price : m), services[0].price)
}

const tabs = computed<Array<{ id: Tab; label: string; count?: () => number | null }>>(() => [
  { id: 'services', label: t('shopDetail.tabs.services'), count: () => aggregatedServices.value.length },
  { id: 'team', label: t('shopDetail.tabs.team'), count: () => shop.value?.members.length ?? 0 },
  { id: 'photos', label: t('shopDetail.tabs.photos'), count: () => shop.value?.photos.length ?? 0 },
])
</script>

<template>
  <CustomerLayout>
    <!-- Back link -->
    <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-5">
      <RouterLink
        to="/customer/explore"
        class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        All barbershops
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
      <h1 class="text-2xl md:text-3xl font-bold text-slate-900 mb-3 tracking-tight">{{ t('shopDetail.notFoundTitle') }}</h1>
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
    <template v-else-if="shop">
      <!-- Identity row: avatar + title (+ meta) + CTA, all inline -->
      <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-6 md:pt-8">
        <div class="flex items-start md:items-center gap-4 md:gap-5 flex-wrap md:flex-nowrap">
          <!-- Avatar -->
          <div
            class="flex-shrink-0 h-14 w-14 md:h-16 md:w-16 rounded-xl overflow-hidden bg-slate-900 text-white flex items-center justify-center text-lg md:text-xl font-bold tracking-tight border border-slate-200"
          >
            <img
              v-if="primaryPhoto"
              :src="primaryPhoto.image"
              :alt="shop.name"
              class="w-full h-full object-cover"
            />
            <span v-else>{{ shopInitials }}</span>
          </div>

          <!-- Title + meta -->
          <div class="flex-1 min-w-0">
            <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight truncate">
              {{ shop.name }}
            </h1>
            <div class="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-slate-600">
              <span class="inline-flex items-center gap-1.5">
                <span
                  :class="[
                    'h-1.5 w-1.5 rounded-full',
                    isOpenNow ? 'bg-emerald-500' : 'bg-slate-400',
                  ]"
                ></span>
                <span class="font-medium" :class="isOpenNow ? 'text-emerald-700' : 'text-slate-700'">
                  {{ isOpenNow ? t('shopDetail.openNow') : t('shopDetail.closed') }}
                </span>
                <span class="text-slate-400">{{ todaysHoursLabel }}</span>
              </span>
            </div>
          </div>

          <!-- CTA -->
          <button
            type="button"
            class="w-full md:w-auto flex-shrink-0 inline-flex items-center justify-center gap-1 px-5 h-11 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
            @click="openBooking"
          >
            {{ t('shopDetail.book') }}
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </section>

      <!-- Sticky tabs -->
      <div class="sticky top-16 z-20 bg-white border-b border-slate-200 mt-4 md:mt-5">
        <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12">
          <nav
            role="tablist"
            aria-label="Shop sections"
            class="flex items-center gap-1 overflow-x-auto -mb-px"
          >
            <button
              v-for="t in tabs"
              :key="t.id"
              role="tab"
              type="button"
              :aria-selected="activeTab === t.id"
              :class="[
                'inline-flex items-center gap-2 px-4 py-3.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap',
                activeTab === t.id
                  ? 'border-slate-900 text-slate-900'
                  : 'border-transparent text-slate-500 hover:text-slate-900',
              ]"
              @click="activeTab = t.id"
            >
              {{ t.label }}
              <span
                v-if="t.count && t.count() !== null && (t.count() as number) > 0"
                :class="[
                  'inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-sm font-semibold rounded-full',
                  activeTab === t.id ? 'bg-slate-900 text-white' : 'bg-slate-100 text-slate-600',
                ]"
              >
                {{ t.count() }}
              </span>
            </button>
          </nav>
        </div>
      </div>

      <!-- Tab content + persistent sidebar -->
      <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-10 md:py-12">
        <div class="grid md:grid-cols-3 gap-8 md:gap-10">
          <!-- Left col: tab-switchable content -->
          <div class="md:col-span-2">
            <!-- SERVICES -->
            <div v-if="activeTab === 'services'">
              <div v-if="aggregatedServices.length === 0" class="text-slate-500">
                {{ t('shopDetail.noServices') }}
              </div>
              <div v-else class="rounded-xl border border-slate-200 overflow-hidden bg-white">
                <div
                  v-for="(service, i) in aggregatedServices"
                  :key="service.name"
                  :class="[
                    'flex items-center justify-between gap-4 px-5 py-4',
                    i < aggregatedServices.length - 1 ? 'border-b border-slate-100' : '',
                  ]"
                >
                  <div class="min-w-0">
                    <p class="text-base font-semibold text-slate-900">{{ service.name }}</p>
                    <p class="text-sm text-slate-500 mt-0.5">
                      {{ t('shopDetail.offeredBy', { count: service.barberCount }, service.barberCount) }}
                    </p>
                  </div>
                  <div class="text-right flex-shrink-0">
                    <p class="text-sm font-semibold text-slate-900 tabular-nums">
                      <span v-if="service.minPrice !== service.maxPrice" class="text-slate-400 font-normal mr-0.5">{{ t('shopDetail.from') }}</span>
                      {{ formatPrice(service.minPrice) }}
                    </p>
                    <button
                      type="button"
                      class="mt-1 text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
                      @click="openBookingForService(service.name)"
                    >
                      {{ t('shopDetail.bookArrow') }}
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- TEAM -->
            <div v-else-if="activeTab === 'team'">
              <div v-if="shop.members.length === 0" class="text-slate-500">
                {{ t('shopDetail.noTeam') }}
              </div>
              <div v-else class="grid grid-cols-1 sm:grid-cols-2 gap-5 md:gap-6">
                <BarberCard
                  v-for="member in shop.members"
                  :key="member.id"
                  :barber="member.barber"
                  :shop-id="shop.id"
                />
              </div>
            </div>

            <!-- PHOTOS -->
            <div v-else-if="activeTab === 'photos'">
              <div v-if="shop.photos.length === 0" class="text-slate-500">
                {{ t('shopDetail.noPhotos') }}
              </div>
              <div v-else class="grid grid-cols-2 md:grid-cols-3 gap-3 md:gap-4">
                <a
                  v-for="photo in shop.photos"
                  :key="photo.id"
                  :href="photo.image"
                  target="_blank"
                  rel="noopener"
                  class="group block aspect-[4/3] rounded-xl overflow-hidden bg-slate-100 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
                >
                  <img
                    :src="photo.image"
                    :alt="shop.name"
                    loading="lazy"
                    class="w-full h-full object-cover transition-transform duration-500 group-hover:scale-[1.03]"
                  />
                </a>
              </div>
            </div>
          </div>

          <!-- Right aside: always visible -->
          <aside class="space-y-8">
            <!-- About -->
            <div v-if="shop.description">
              <h2 class="text-lg font-semibold text-slate-900 mb-3 tracking-tight">{{ t('shopDetail.about') }}</h2>
              <p class="text-[15px] text-slate-700 leading-relaxed">
                {{ shop.description }}
              </p>
            </div>

            <!-- Location -->
            <div>
              <h2 class="text-lg font-semibold text-slate-900 mb-3 tracking-tight">{{ t('shopDetail.location') }}</h2>
              <div
                v-if="mapCenter"
                class="relative isolate rounded-xl overflow-hidden aspect-[4/3] border border-slate-200"
              >
                <LMap
                  :zoom="15"
                  :center="mapCenter"
                  :use-global-leaflet="true"
                  :dragging="false"
                  :scroll-wheel-zoom="false"
                  :zoom-control="false"
                  :double-click-zoom="false"
                  :attribution-control="false"
                  style="height: 100%; width: 100%;"
                >
                  <LTileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                  <LMarker :lat-lng="mapCenter" />
                </LMap>
              </div>
              <div
                v-else
                class="rounded-xl aspect-[4/3] border border-dashed border-slate-200 flex items-center justify-center text-sm text-slate-400"
              >
                Location not set
              </div>
              <p class="mt-3 flex items-start gap-2 text-sm text-slate-600">
                <svg class="h-4 w-4 flex-shrink-0 mt-0.5 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>{{ shop.address }}</span>
              </p>
            </div>

            <!-- Opening hours -->
            <div>
              <h2 class="text-lg font-semibold text-slate-900 mb-3 tracking-tight">{{ t('shopDetail.openingHours') }}</h2>
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
                    <template v-if="getHoursForDay(i)?.is_open">
                      {{ formatTime(getHoursForDay(i)?.opens_at ?? null) }}
                      <span class="text-slate-300 mx-1">–</span>
                      {{ formatTime(getHoursForDay(i)?.closes_at ?? null) }}
                    </template>
                    <span v-else class="text-slate-400">{{ t('shopDetail.closedToday') }}</span>
                  </dd>
                </div>
              </dl>
            </div>
          </aside>
        </div>
      </section>

      <!-- Book appointment modal -->
      <Teleport to="body">
        <Transition name="fade">
          <div
            v-if="isBookOpen"
            class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-end md:items-center justify-center md:p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="book-modal-title"
            @click.self="closeBooking"
          >
            <Transition name="slide-up">
              <div
                v-if="isBookOpen"
                class="w-full md:max-w-lg bg-white rounded-t-2xl md:rounded-2xl shadow-xl flex flex-col max-h-[85vh]"
              >
                <!-- Header -->
                <div class="flex items-start justify-between gap-4 px-5 md:px-6 py-4 border-b border-slate-200">
                  <div class="min-w-0">
                    <p class="text-sm font-medium text-slate-500 uppercase tracking-wide mb-0.5">
                      {{ bookingServiceName ? `Book · ${bookingServiceName}` : 'Book at' }}
                    </p>
                    <h2 id="book-modal-title" class="text-lg font-semibold text-slate-900 tracking-tight truncate">
                      {{ shop.name }}
                    </h2>
                  </div>
                  <button
                    type="button"
                    aria-label="Close"
                    class="flex-shrink-0 h-9 w-9 inline-flex items-center justify-center rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                    @click="closeBooking"
                  >
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <!-- Body: barber list -->
                <div class="flex-1 overflow-y-auto">
                  <p class="px-5 md:px-6 pt-4 pb-2 text-sm text-slate-600">
                    <template v-if="bookingServiceName">
                      Offered by {{ bookingMembers.length }}
                      {{ bookingMembers.length === 1 ? 'barber' : 'barbers' }} — pick one to see available times.
                    </template>
                    <template v-else>
                      Choose a barber to see available times.
                    </template>
                  </p>

                  <div v-if="bookingMembers.length === 0" class="px-5 md:px-6 py-10 text-center text-slate-500 text-sm">
                    No barbers available.
                  </div>

                  <ul v-else class="px-2 md:px-3 pb-3">
                    <li v-for="member in bookingMembers" :key="member.id">
                      <div
                        class="flex items-center gap-4 px-3 md:px-4 py-3 rounded-lg hover:bg-slate-50 transition-colors"
                      >
                        <!-- Avatar -->
                        <div class="flex-shrink-0 h-11 w-11 rounded-full overflow-hidden bg-slate-100 border border-slate-200">
                          <img
                            v-if="member.barber.avatar"
                            :src="member.barber.avatar"
                            :alt="member.barber.full_name"
                            class="w-full h-full object-cover"
                          />
                          <div v-else class="w-full h-full flex items-center justify-center text-slate-400">
                            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.4" viewBox="0 0 24 24">
                              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                          </div>
                        </div>

                        <!-- Info -->
                        <div class="flex-1 min-w-0">
                          <p class="text-sm font-semibold text-slate-900 truncate">
                            {{ member.barber.full_name }}
                          </p>
                          <p v-if="member.barber.top_services.length > 0" class="text-sm text-slate-500 truncate mt-0.5">
                            {{ member.barber.top_services.slice(0, 3).map(s => s.name).join(' · ') }}
                          </p>
                          <p v-else class="text-sm text-slate-400 mt-0.5">
                            Services on arrival
                          </p>
                        </div>

                        <!-- Book button -->
                        <RouterLink
                          :to="{ name: 'customer-booking', params: { barberId: member.barber.id } }"
                          class="flex-shrink-0 inline-flex items-center gap-1 px-3.5 h-9 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
                          @click="closeBooking"
                        >
                          Book
                          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                          </svg>
                        </RouterLink>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </Transition>
          </div>
        </Transition>
      </Teleport>
    </template>
  </CustomerLayout>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.18s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(16px);
  opacity: 0;
}
@media (min-width: 768px) {
  .slide-up-enter-from,
  .slide-up-leave-to {
    transform: scale(0.97);
  }
}
</style>
