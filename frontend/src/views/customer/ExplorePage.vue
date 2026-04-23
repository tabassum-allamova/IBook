<script setup lang="ts">
import { ref, computed, toRaw, onMounted, shallowRef, markRaw, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery } from '@tanstack/vue-query'
import { useDebounceFn } from '@vueuse/core'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'vue-leaflet-markercluster/dist/style.css'

// REQUIRED: markercluster needs Leaflet on globalThis
;(globalThis as unknown as Record<string, unknown>).L = L

// Vite icon fix — prevents broken marker images
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

import { LMap, LTileLayer, LMarker, LPopup } from '@vue-leaflet/vue-leaflet'
import { LMarkerClusterGroup } from 'vue-leaflet-markercluster'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import ShopCard from '@/components/discovery/ShopCard.vue'
import ShopFilterModal from '@/components/discovery/ShopFilterModal.vue'
import type { ShopListItem } from '@/components/discovery/ShopCard.vue'
import api from '@/lib/axios'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const { t } = useI18n()

function goToSearch(patch: Record<string, string | number | null | undefined> = {}) {
  const query: Record<string, string> = {}
  for (const [k, v] of Object.entries(patch)) {
    if (v === null || v === undefined || v === '') continue
    query[k] = String(v)
  }
  router.push({ name: 'customer-search', query })
}

// ---- Geolocation (Pattern 2 from RESEARCH.md) ----
// NOTE: Leaflet recurses infinitely when it reads Vue Proxy objects
// (extend → LatLngBounds → toLatLngBounds). Use shallowRef + markRaw
// for any coordinate data so Leaflet only ever sees plain arrays.
const TASHKENT = markRaw<[number, number]>([41.2995, 69.2401])
const center = shallowRef<[number, number]>(TASHKENT)
const locationDenied = ref(false)
const lat = ref<number | null>(null)
const lng = ref<number | null>(null)

const GEO_CACHE_KEY = 'ibook.geolocation'
const GEO_TTL_MS = 24 * 60 * 60 * 1000 // 24h — skip browser geolocation on refresh

function readCachedLocation(): { lat: number; lng: number } | null {
  try {
    const raw = localStorage.getItem(GEO_CACHE_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as { lat?: unknown; lng?: unknown; ts?: unknown }
    if (
      typeof parsed.lat !== 'number' ||
      typeof parsed.lng !== 'number' ||
      typeof parsed.ts !== 'number' ||
      Date.now() - parsed.ts > GEO_TTL_MS
    ) {
      return null
    }
    return { lat: parsed.lat, lng: parsed.lng }
  } catch {
    return null
  }
}

function writeCachedLocation(latVal: number, lngVal: number) {
  try {
    localStorage.setItem(
      GEO_CACHE_KEY,
      JSON.stringify({ lat: latVal, lng: lngVal, ts: Date.now() }),
    )
  } catch {
    // storage unavailable (private mode / quota) — fine, we just won't cache
  }
}

onMounted(() => {
  const cached = readCachedLocation()
  if (cached) {
    lat.value = cached.lat
    lng.value = cached.lng
    center.value = markRaw<[number, number]>([cached.lat, cached.lng])
    return
  }
  if (!navigator.geolocation) {
    locationDenied.value = true
    return
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      lat.value = pos.coords.latitude
      lng.value = pos.coords.longitude
      center.value = markRaw<[number, number]>([pos.coords.latitude, pos.coords.longitude])
      writeCachedLocation(pos.coords.latitude, pos.coords.longitude)
    },
    () => {
      locationDenied.value = true
      center.value = TASHKENT
    },
    { timeout: 5000, maximumAge: GEO_TTL_MS },
  )
})

// ---- View mode ----
const viewMode = ref<'list' | 'map'>('list')

// ---- Filter modal ----
const isFilterOpen = ref(false)

// ---- Filter state ----
const searchName = ref('')
const minRating = ref(0)
const sortBy = ref('distance')
const minPrice = ref<number | null>(null)
const maxPrice = ref<number | null>(null)
const selectedRegion = ref('')

// Regions of Uzbekistan. `aliases` covers common Latin/Uzbek spellings so
// the address-substring match works regardless of how a shop was seeded.
const REGIONS: { label: string; aliases: string[] }[] = [
  { label: 'Tashkent', aliases: ['tashkent', 'toshkent'] },
  { label: 'Andijan', aliases: ['andijan', 'andijon'] },
  { label: 'Bukhara', aliases: ['bukhara', 'buxoro', 'bukhoro'] },
  { label: 'Fergana', aliases: ['fergana', "farg'ona", 'fargona'] },
  { label: 'Jizzakh', aliases: ['jizzakh', 'jizzax'] },
  { label: 'Karakalpakstan', aliases: ['karakalpakstan', "qoraqalpog'iston", 'qoraqalpogiston'] },
  { label: 'Kashkadarya', aliases: ['kashkadarya', 'qashqadaryo'] },
  { label: 'Khorezm', aliases: ['khorezm', 'xorazm'] },
  { label: 'Namangan', aliases: ['namangan'] },
  { label: 'Navoi', aliases: ['navoi', 'navoiy'] },
  { label: 'Samarkand', aliases: ['samarkand', 'samarqand'] },
  { label: 'Sirdaryo', aliases: ['sirdaryo', 'syrdarya'] },
  { label: 'Surkhandarya', aliases: ['surkhandarya', 'surxondaryo'] },
]

// Count of active filters (excludes search + default sort — those live outside the modal trigger badge)
const activeFilterCount = computed(() => {
  let n = 0
  if (minRating.value > 0) n++
  if (minPrice.value !== null) n++
  if (maxPrice.value !== null) n++
  if (sortBy.value !== 'distance') n++
  return n
})

function clearFilters() {
  minRating.value = 0
  minPrice.value = null
  maxPrice.value = null
  sortBy.value = 'distance'
}

// Navigate to the full search page when the user commits a query.
const commitSearch = useDebounceFn((v: string) => {
  const trimmed = v.trim()
  if (trimmed.length === 0) return
  goToSearch({ q: trimmed })
}, 400)

function onSearchInput(e: Event) {
  const v = (e.target as HTMLInputElement).value
  searchName.value = v
  commitSearch(v)
}

function onSearchSubmit(e: Event) {
  e.preventDefault()
  const trimmed = searchName.value.trim()
  if (trimmed.length === 0) return
  goToSearch({ q: trimmed })
}

function clearSearch() {
  searchName.value = ''
}

watch(selectedRegion, (region) => {
  if (region) {
    goToSearch({ region })
    // reset so returning to landing is clean
    selectedRegion.value = ''
  }
})

watch(
  [minRating, minPrice, maxPrice, sortBy],
  ([rating, lo, hi, sort]) => {
    const hasAny = rating > 0 || lo !== null || hi !== null || (sort && sort !== 'distance')
    if (!hasAny) return
    goToSearch({
      rating: rating > 0 ? rating : null,
      minPrice: lo,
      maxPrice: hi,
      sort: sort && sort !== 'distance' ? sort : null,
    })
    // reset so landing state stays clean
    minRating.value = 0
    minPrice.value = null
    maxPrice.value = null
    sortBy.value = 'distance'
    isFilterOpen.value = false
  },
)

// ---- Data fetching (Pattern 4 from RESEARCH.md) ----
const { data: rawShops, isLoading } = useQuery({
  queryKey: computed(() => ['shops', lat.value, lng.value]),
  queryFn: async () => {
    const params: Record<string, string | number> = {}
    if (lat.value !== null) params.lat = lat.value
    if (lng.value !== null) params.lng = lng.value
    const res = await api.get('/api/shops/', { params })
    return res.data as ShopListItem[]
  },
})

const shops = computed(() => rawShops.value ?? [])

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function buildShopIcon(shop: ShopListItem): L.DivIcon {
  const initial = (shop.name?.trim()?.[0] ?? '?').toUpperCase()
  const inner = shop.photo
    ? `<img src="${escapeHtml(shop.photo)}" alt="" loading="lazy" />`
    : `<span class="pin-marker__initial">${escapeHtml(initial)}</span>`
  return L.divIcon({
    className: 'pin-marker pin-marker--shop',
    html: `<div class="pin-marker__bubble">${inner}</div><div class="pin-marker__tail"></div>`,
    iconSize: [44, 54],
    iconAnchor: [22, 54],
    popupAnchor: [0, -50],
  })
}

function buildBarberIcon(b: SoloBarber): L.DivIcon {
  const initial = (b.full_name?.trim()?.[0] ?? '?').toUpperCase()
  const inner = b.avatar
    ? `<img src="${escapeHtml(b.avatar)}" alt="" loading="lazy" />`
    : `<span class="pin-marker__initial">${escapeHtml(initial)}</span>`
  return L.divIcon({
    className: 'pin-marker pin-marker--barber',
    html: `<div class="pin-marker__bubble">${inner}</div><div class="pin-marker__tail"></div>`,
    iconSize: [44, 54],
    iconAnchor: [22, 54],
    popupAnchor: [0, -50],
  })
}

// Shops that have coordinates (for map pins).
// Pre-compute a non-reactive [lat, lng] tuple for Leaflet — passing a
// Vue Proxy through to LMarker triggers Leaflet's extend/toLatLngBounds
// recursion.
const shopsWithCoords = computed(() =>
  shops.value
    .filter((s): s is ShopListItem & { lat: number; lng: number } =>
      s.lat !== null && s.lng !== null,
    )
    .map((s) => ({
      ...s,
      position: markRaw<[number, number]>([Number(s.lat), Number(s.lng)]),
      icon: markRaw(buildShopIcon(s)),
    })),
)

const soloBarbersWithCoords = computed(() =>
  (soloBarbers.value ?? [])
    .filter((b) => b.lat !== null && b.lng !== null)
    .map((b) => ({
      ...b,
      position: markRaw<[number, number]>([Number(b.lat), Number(b.lng)]),
      icon: markRaw(buildBarberIcon(b)),
    })),
)

// ---- Map-list sync (Pattern 1 from RESEARCH.md) ----
const mapRef = ref()
const visibleShopIds = ref<Set<number>>(new Set())

function updateVisibleShops() {
  const map = toRaw(mapRef.value)?.leafletObject
  if (!map) return
  const bounds = map.getBounds()
  visibleShopIds.value = new Set(
    shopsWithCoords.value
      .filter((s) => bounds.contains(s.position))
      .map((s) => s.id),
  )
}

function onMapReady() {
  updateVisibleShops()
}

function onMoveEnd() {
  updateVisibleShops()
}

// Shops visible in current map viewport (before additional client-side filters).
// Only apply bounds filter when map view is active — in list view, show all shops.
const visibleShops = computed(() => {
  if (viewMode.value !== 'map') return shops.value
  if (visibleShopIds.value.size === 0) return shops.value
  return shops.value.filter((s) => visibleShopIds.value.has(s.id))
})

// ---- filteredVisibleShops: apply all client-side filters ----
const filteredVisibleShops = computed(() => {
  let result = visibleShops.value

  if (selectedRegion.value) {
    const region = REGIONS.find((r) => r.label === selectedRegion.value)
    if (region) {
      result = result.filter((s) => {
        const addr = (s.address ?? '').toLowerCase()
        return region.aliases.some((a) => addr.includes(a))
      })
    }
  }

  if (minRating.value > 0) {
    result = result.filter(
      (s) => s.avg_rating !== null && s.avg_rating >= minRating.value,
    )
  }

  if (minPrice.value !== null) {
    result = result.filter(
      (s) => s.min_price !== null && s.min_price >= (minPrice.value as number),
    )
  }

  if (maxPrice.value !== null) {
    result = result.filter(
      (s) => s.min_price !== null && s.min_price <= (maxPrice.value as number),
    )
  }

  if (sortBy.value === 'name') {
    result = [...result].sort((a, b) => a.name.localeCompare(b.name))
  }

  return result
})

const MAX_LANDING_RESULTS = 6
const topShops = computed(() => filteredVisibleShops.value.slice(0, MAX_LANDING_RESULTS))

// ---- Solo barbers (no shop affiliation) ----
interface SoloBarber {
  id: number
  full_name: string
  avatar: string | null
  years_of_experience: number | null
  min_price: number | null
  avg_rating: number | null
  top_service_names: string[]
  lat: string | number | null
  lng: string | number | null
}

const { data: soloBarbers } = useQuery<SoloBarber[]>({
  queryKey: ['barbers', 'solo'],
  queryFn: async () => {
    const res = await api.get<SoloBarber[]>('/api/barbers/', { params: { solo: 'true' } })
    return res.data
  },
})

function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-US').format(amount) + ' UZS'
}
</script>

<template>
  <CustomerLayout>
    <!-- Hero -->
    <section class="bg-white border-b border-slate-100">
      <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-10 md:pt-16 pb-6 md:pb-10">
        <h1 class="text-3xl md:text-5xl font-bold text-slate-900 tracking-tight leading-[1.1] max-w-3xl">
          {{ t('explore.heroTitle') }}
        </h1>
        <p class="mt-4 text-base md:text-lg text-slate-600 max-w-2xl leading-relaxed">
          {{ t('explore.heroSubtitle') }}
        </p>
      </div>
    </section>

    <!-- Location denied inline banner -->
    <div
      v-if="locationDenied"
      class="bg-amber-50 border-b border-amber-200"
    >
      <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-3 flex items-center gap-3">
        <svg class="h-4 w-4 text-amber-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <p class="text-sm text-amber-900">
          {{ t('explore.locationOff') }}
        </p>
      </div>
    </div>

    <!-- Toolbar: search + Filters button + List/Map toggle (sticky) -->
    <section class="bg-white sticky top-16 z-30">
      <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-4 flex items-center gap-3">
        <!-- Search -->
        <label class="relative flex-1 min-w-0">
          <span class="sr-only">{{ t('explore.searchLabel') }}</span>
          <svg
            class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
            />
          </svg>
          <input
            type="text"
            :value="searchName"
            :placeholder="t('explore.searchPlaceholder')"
            class="w-full h-10 pl-10 pr-9 text-sm bg-white border border-slate-200 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition"
            @input="onSearchInput"
            @keydown.enter="onSearchSubmit"
          />
          <button
            v-if="searchName"
            type="button"
            aria-label="Clear search"
            class="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 inline-flex items-center justify-center rounded-md text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            @click="clearSearch"
          >
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </label>

        <!-- Region select -->
        <label class="relative flex-shrink-0">
          <span class="sr-only">Region</span>
          <select
            v-model="selectedRegion"
            class="appearance-none h-10 pl-3 pr-8 text-sm bg-white border border-slate-200 rounded-lg text-slate-900 hover:border-slate-400 focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition cursor-pointer w-32 md:w-44"
          >
            <option value="">All regions</option>
            <option v-for="r in REGIONS" :key="r.label" :value="r.label">
              {{ r.label }}
            </option>
          </select>
          <svg
            class="absolute right-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500 pointer-events-none"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </label>

        <!-- Filters button -->
        <button
          type="button"
          aria-label="Open filters"
          :class="[
            'relative inline-flex items-center gap-2 h-10 px-3.5 rounded-lg border text-sm font-medium transition-colors flex-shrink-0',
            activeFilterCount > 0
              ? 'bg-slate-900 text-white border-slate-900 hover:bg-slate-800'
              : 'bg-white text-slate-700 border-slate-200 hover:border-slate-400',
          ]"
          @click="isFilterOpen = true"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 4.5h18M6 12h12M10 19.5h4" />
          </svg>
          <span class="hidden sm:inline">{{ t('explore.filtersButton') }}</span>
          <span
            v-if="activeFilterCount > 0"
            :class="[
              'inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-[11px] font-semibold rounded-full',
              activeFilterCount > 0 ? 'bg-white text-slate-900' : 'bg-slate-900 text-white',
            ]"
          >
            {{ activeFilterCount }}
          </span>
        </button>

        <!-- List/Map toggle -->
        <div
          role="tablist"
          aria-label="View mode"
          class="inline-flex items-center h-10 rounded-lg border border-slate-200 bg-white p-0.5 flex-shrink-0"
        >
          <button
            role="tab"
            type="button"
            :aria-selected="viewMode === 'list'"
            :class="[
              'inline-flex items-center gap-1.5 h-full px-3 text-[13px] font-medium rounded-md transition-colors',
              viewMode === 'list'
                ? 'bg-slate-900 text-white'
                : 'text-slate-600 hover:text-slate-900',
            ]"
            @click="viewMode = 'list'"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
            <span class="hidden sm:inline">{{ t('explore.listView') }}</span>
          </button>
          <button
            role="tab"
            type="button"
            :aria-selected="viewMode === 'map'"
            :class="[
              'inline-flex items-center gap-1.5 h-full px-3 text-[13px] font-medium rounded-md transition-colors',
              viewMode === 'map'
                ? 'bg-slate-900 text-white'
                : 'text-slate-600 hover:text-slate-900',
            ]"
            @click="viewMode = 'map'"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l5.553 2.776A1 1 0 0022 18.882V8.118a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
            </svg>
            <span class="hidden sm:inline">{{ t('explore.mapView') }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Content: list OR map -->
    <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-3 pb-16 md:pb-20">
      <!-- LIST VIEW -->
      <template v-if="viewMode === 'list'">
        <!-- Loading skeletons -->
        <div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
          <div v-for="n in 6" :key="n" class="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div class="aspect-[4/3] bg-slate-100 animate-pulse" />
            <div class="p-5 space-y-3">
              <div class="h-5 bg-slate-100 animate-pulse rounded w-3/4" />
              <div class="h-3 bg-slate-100 animate-pulse rounded w-1/2" />
              <div class="h-10 bg-slate-100 animate-pulse rounded" />
            </div>
          </div>
        </div>

        <!-- Empty -->
        <div
          v-else-if="filteredVisibleShops.length === 0"
          class="bg-white rounded-xl border border-slate-200 py-16 px-6 text-center"
        >
          <svg class="h-10 w-10 text-slate-300 mx-auto mb-3" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <p class="text-lg font-semibold text-slate-900 mb-1">{{ t('explore.noResults') }}</p>
          <p class="text-sm text-slate-500">{{ t('explore.noResultsHint') }}</p>
        </div>

        <!-- Grid -->
        <div
          v-else
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6"
        >
          <ShopCard
            v-for="shop in topShops"
            :key="shop.id"
            :shop="shop"
          />
        </div>
      </template>

      <!-- MAP VIEW -->
      <div
        v-else
        class="rounded-xl overflow-hidden border border-slate-200 bg-white"
      >
        <LMap
          ref="mapRef"
          :zoom="13"
          :center="center"
          :use-global-leaflet="true"
          style="height: 70vh"
          class="z-0"
          @moveend="onMoveEnd"
          @ready="onMapReady"
        >
          <LTileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
          />
          <LMarkerClusterGroup>
            <!-- Shops -->
            <LMarker
              v-for="shop in shopsWithCoords"
              :key="`shop-${shop.id}`"
              :lat-lng="shop.position"
              :icon="shop.icon"
            >
              <LPopup>
                <article class="ibook-popup">
                  <div class="ibook-popup__media">
                    <img
                      v-if="shop.photo"
                      :src="shop.photo"
                      :alt="shop.name"
                      class="w-full h-full object-cover"
                    />
                    <div v-else class="ibook-popup__media-fallback">
                      <svg class="h-10 w-10" fill="none" stroke="currentColor" stroke-width="1.4" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16" />
                      </svg>
                    </div>
                    <span class="ibook-popup__chip ibook-popup__chip--left">
                      <span
                        class="h-1.5 w-1.5 rounded-full"
                        :class="shop.is_open_now ? 'bg-emerald-500' : 'bg-slate-400'"
                      ></span>
                      {{ shop.is_open_now ? 'Open now' : 'Closed' }}
                    </span>
                    <span
                      v-if="shop.avg_rating !== null"
                      class="ibook-popup__chip ibook-popup__chip--right"
                    >
                      <svg class="h-3.5 w-3.5 text-amber-400 fill-current" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      {{ shop.avg_rating.toFixed(1) }}
                    </span>
                  </div>
                  <div class="ibook-popup__body">
                    <h3 class="ibook-popup__title">{{ shop.name }}</h3>
                    <p v-if="shop.address" class="ibook-popup__meta">
                      <svg class="h-3.5 w-3.5 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                      <span class="truncate">{{ shop.address }}</span>
                    </p>
                    <div class="ibook-popup__footer">
                      <div>
                        <p v-if="shop.min_price !== null" class="text-sm text-slate-600">
                          <span class="text-slate-400">From</span>
                          <span class="ml-1 font-semibold text-slate-900">{{ new Intl.NumberFormat('en-US').format(shop.min_price) }} UZS</span>
                        </p>
                        <p v-else class="text-sm text-slate-400">Price on arrival</p>
                      </div>
                      <RouterLink
                        :to="{ name: 'customer-shop-detail', params: { shopId: shop.id } }"
                        class="ibook-popup__cta"
                      >
                        View
                        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                      </RouterLink>
                    </div>
                  </div>
                </article>
              </LPopup>
            </LMarker>

            <!-- Solo barbers -->
            <LMarker
              v-for="b in soloBarbersWithCoords"
              :key="`barber-${b.id}`"
              :lat-lng="b.position"
              :icon="b.icon"
            >
              <LPopup>
                <article class="ibook-popup">
                  <div class="ibook-popup__media">
                    <img
                      v-if="b.avatar"
                      :src="b.avatar"
                      :alt="b.full_name"
                      class="w-full h-full object-cover"
                    />
                    <div v-else class="ibook-popup__media-fallback">
                      <svg class="h-10 w-10" fill="none" stroke="currentColor" stroke-width="1.4" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                      </svg>
                    </div>
                    <span class="ibook-popup__chip ibook-popup__chip--left">
                      <span class="h-1.5 w-1.5 rounded-full bg-slate-900"></span>
                      Solo
                    </span>
                    <span
                      v-if="b.avg_rating !== null"
                      class="ibook-popup__chip ibook-popup__chip--right"
                    >
                      <svg class="h-3.5 w-3.5 text-amber-400 fill-current" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      {{ b.avg_rating.toFixed(1) }}
                    </span>
                  </div>
                  <div class="ibook-popup__body">
                    <h3 class="ibook-popup__title">{{ b.full_name }}</h3>
                    <p v-if="b.top_service_names.length > 0" class="ibook-popup__meta">
                      <svg class="h-3.5 w-3.5 text-slate-400 flex-shrink-0" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
                        <circle cx="12" cy="12" r="9" />
                      </svg>
                      <span class="truncate">{{ b.top_service_names.join(' · ') }}</span>
                    </p>
                    <div class="ibook-popup__footer">
                      <div>
                        <p v-if="b.min_price !== null" class="text-sm text-slate-600">
                          <span class="text-slate-400">From</span>
                          <span class="ml-1 font-semibold text-slate-900">{{ new Intl.NumberFormat('en-US').format(b.min_price) }} UZS</span>
                        </p>
                        <p v-else class="text-sm text-slate-400">Price on arrival</p>
                      </div>
                      <RouterLink
                        :to="{ name: 'customer-barber-profile', params: { barberId: b.id } }"
                        class="ibook-popup__cta"
                      >
                        View
                        <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                          <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                        </svg>
                      </RouterLink>
                    </div>
                  </div>
                </article>
              </LPopup>
            </LMarker>
          </LMarkerClusterGroup>
        </LMap>
      </div>
    </section>

    <!-- Independent barbers -->
    <section
      v-if="soloBarbers && soloBarbers.length > 0"
      class="bg-white border-t border-slate-100"
    >
      <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-12 md:py-16">
        <div class="flex items-end justify-between gap-4 mb-8 md:mb-10">
          <div class="max-w-2xl">
            <p class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">{{ t('explore.independent') }}</p>
            <h2 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
              Solo barbers near you
            </h2>
            <p class="mt-2 text-sm md:text-base text-slate-600 leading-relaxed">
              Skilled cutters who work on their own — book directly, no shop booking required.
            </p>
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
          <RouterLink
            v-for="b in soloBarbers.slice(0, 6)"
            :key="b.id"
            :to="{ name: 'customer-barber-profile', params: { barberId: b.id } }"
            class="group block bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all overflow-hidden focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
          >
            <!-- Photo / avatar -->
            <div class="relative aspect-[4/3] overflow-hidden bg-slate-100">
              <img
                v-if="b.avatar"
                :src="b.avatar"
                :alt="b.full_name"
                class="w-full h-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.03]"
                loading="lazy"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <svg
                  class="h-14 w-14 text-slate-300"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.2"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>

              <!-- Solo chip -->
              <span
                class="absolute top-3 left-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-semibold bg-white text-slate-700 shadow-sm"
              >
                <span class="h-1.5 w-1.5 rounded-full bg-slate-900"></span>
                Solo
              </span>

              <!-- Rating chip -->
              <span
                v-if="b.avg_rating !== null"
                class="absolute top-3 right-3 inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-sm font-semibold bg-white text-slate-900 shadow-sm"
              >
                <svg class="h-3.5 w-3.5 text-amber-400 fill-current" viewBox="0 0 20 20">
                  <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                </svg>
                {{ b.avg_rating.toFixed(1) }}
              </span>
            </div>

            <!-- Content -->
            <div class="p-5">
              <h3 class="text-lg font-semibold text-slate-900 mb-1 line-clamp-1 tracking-tight">
                {{ b.full_name }}
              </h3>

              <!-- Services / experience -->
              <p class="flex items-center gap-1.5 text-sm text-slate-500 mb-4 line-clamp-1">
                <svg class="h-3.5 w-3.5 flex-shrink-0 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6l4 2" />
                  <circle cx="12" cy="12" r="9" />
                </svg>
                <span class="truncate">
                  <template v-if="b.top_service_names.length > 0">
                    {{ b.top_service_names.join(' · ') }}
                  </template>
                  <template v-else-if="b.years_of_experience !== null">
                    {{ b.years_of_experience }} {{ b.years_of_experience === 1 ? 'yr' : 'yrs' }} experience
                  </template>
                  <template v-else>
                    Services on arrival
                  </template>
                </span>
              </p>

              <!-- Footer: price + CTA -->
              <div class="flex items-center justify-between pt-3 border-t border-slate-100">
                <div class="min-w-0">
                  <p class="text-sm font-medium uppercase tracking-wide text-slate-400">{{ t('explore.from') }}</p>
                  <p v-if="b.min_price !== null" class="text-base font-semibold text-slate-900">
                    {{ formatPrice(b.min_price) }}
                  </p>
                  <p v-else class="text-sm text-slate-400">On arrival</p>
                </div>
                <span
                  class="inline-flex items-center gap-1 text-sm font-semibold text-slate-900 group-hover:gap-1.5 transition-all"
                >
                  View
                  <svg class="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </span>
              </div>
            </div>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="bg-slate-50 border-t border-slate-100">
      <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-16 md:py-20">
        <div class="max-w-2xl mb-10 md:mb-12">
          <p class="text-sm font-semibold text-slate-500 uppercase tracking-wide mb-3">How it works</p>
          <h2 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
            Three steps to a fresh cut.
          </h2>
        </div>

        <div class="grid md:grid-cols-3 gap-6 md:gap-8">
          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-slate-900 text-white font-semibold mb-4">
              1
            </div>
            <h3 class="text-lg font-semibold text-slate-900 mb-2">Find a shop</h3>
            <p class="text-sm text-slate-600 leading-relaxed">
              See barbershops on a map with ratings, prices, and opening hours. Filter by whatever matters to you.
            </p>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-slate-900 text-white font-semibold mb-4">
              2
            </div>
            <h3 class="text-lg font-semibold text-slate-900 mb-2">Pick a slot</h3>
            <p class="text-sm text-slate-600 leading-relaxed">
              Real schedules, updated as bookings come in. Choose a barber, a service, and a time that works.
            </p>
          </div>

          <div class="bg-white rounded-xl border border-slate-200 p-6">
            <div class="inline-flex items-center justify-center h-10 w-10 rounded-lg bg-slate-900 text-white font-semibold mb-4">
              3
            </div>
            <h3 class="text-lg font-semibold text-slate-900 mb-2">Show up</h3>
            <p class="text-sm text-slate-600 leading-relaxed">
              Pay online or at the shop. Reschedule from your phone if plans change — no phone calls needed.
            </p>
          </div>
        </div>
      </div>
    </section>

    <!-- Testimonial -->
    <section class="bg-white border-t border-slate-100">
      <div class="max-w-3xl mx-auto px-5 md:px-8 lg:px-12 py-16 md:py-20 text-center">
        <div class="flex items-center justify-center gap-0.5 mb-6">
          <svg v-for="n in 5" :key="n" class="h-5 w-5 text-amber-400 fill-current" viewBox="0 0 20 20">
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        </div>
        <p class="text-xl md:text-2xl text-slate-900 font-medium leading-snug mb-6">
          “I used to spend twenty minutes on WhatsApp trying to get a chair for Saturday. Now it's six taps and I'm done.”
        </p>
        <div class="flex items-center justify-center gap-3">
          <div class="h-10 w-10 rounded-full bg-slate-100 flex items-center justify-center text-slate-600 font-semibold">
            A
          </div>
          <div class="text-left">
            <p class="text-sm font-semibold text-slate-900">Aziz R.</p>
            <p class="text-xs text-slate-500">Customer, Tashkent</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="bg-slate-900">
      <div class="max-w-5xl mx-auto px-5 md:px-8 lg:px-12 py-14 md:py-20 text-center">
        <h2 class="text-3xl md:text-4xl font-bold text-white tracking-tight mb-4">
          Ready for your next cut?
        </h2>
        <p class="text-slate-300 text-base md:text-lg max-w-xl mx-auto mb-8">
          Create a free account to save your favourite barbers, track appointments, and book again in one tap.
        </p>
        <div class="flex flex-wrap items-center justify-center gap-3">
          <template v-if="!auth.isAuthenticated">
            <RouterLink
              to="/register/customer"
              class="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-white hover:bg-slate-100 text-slate-900 font-semibold transition-colors"
            >
              Sign up as a customer
            </RouterLink>
            <RouterLink
              to="/register/professional"
              class="inline-flex items-center justify-center px-6 py-3 rounded-lg border border-slate-700 hover:border-slate-500 text-white font-semibold transition-colors"
            >
              I'm a barber or shop owner
            </RouterLink>
          </template>
          <template v-else>
            <RouterLink
              to="/customer/appointments"
              class="inline-flex items-center justify-center px-6 py-3 rounded-lg bg-white hover:bg-slate-100 text-slate-900 font-semibold transition-colors"
            >
              Go to my appointments
            </RouterLink>
          </template>
        </div>
      </div>
    </section>

    <!-- Footer -->
    <footer class="bg-white border-t border-slate-200">
      <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-12 md:py-14">
        <div class="flex flex-col md:flex-row gap-8 md:gap-12 md:items-start md:justify-between">
          <div class="max-w-xs">
            <div class="flex items-center gap-2 mb-3">
              <span class="inline-flex items-center justify-center h-8 w-8 rounded-md bg-slate-900 text-white text-sm font-bold">i</span>
              <span class="text-lg font-semibold text-slate-900 tracking-tight">IBook</span>
            </div>
            <p class="text-sm text-slate-600 leading-relaxed">
              Tashkent's online barbershop directory. Book a chair with the best cutters in the city.
            </p>
          </div>

          <div class="grid grid-cols-2 sm:grid-cols-3 gap-8 text-sm">
            <div>
              <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Discover</p>
              <ul class="space-y-2">
                <li><RouterLink to="/customer/explore" class="text-slate-600 hover:text-slate-900 transition-colors">Explore shops</RouterLink></li>
                <li><a href="#" class="text-slate-600 hover:text-slate-900 transition-colors">Top rated</a></li>
                <li><a href="#" class="text-slate-600 hover:text-slate-900 transition-colors">Open now</a></li>
              </ul>
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">For pros</p>
              <ul class="space-y-2">
                <li><RouterLink to="/register/professional" class="text-slate-600 hover:text-slate-900 transition-colors">Join as a barber</RouterLink></li>
                <li><RouterLink to="/register/professional" class="text-slate-600 hover:text-slate-900 transition-colors">List your shop</RouterLink></li>
                <li><RouterLink to="/login" class="text-slate-600 hover:text-slate-900 transition-colors">Log in</RouterLink></li>
              </ul>
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Company</p>
              <ul class="space-y-2">
                <li><a href="#" class="text-slate-600 hover:text-slate-900 transition-colors">About</a></li>
                <li><a href="#" class="text-slate-600 hover:text-slate-900 transition-colors">Privacy</a></li>
                <li><a href="#" class="text-slate-600 hover:text-slate-900 transition-colors">Contact</a></li>
              </ul>
            </div>
          </div>
        </div>

        <div class="mt-10 pt-6 border-t border-slate-200 flex flex-col sm:flex-row gap-2 sm:items-center sm:justify-between text-xs text-slate-500">
          <p>© {{ new Date().getFullYear() }} IBook. All rights reserved.</p>
          <p>Made in Tashkent.</p>
        </div>
      </div>
    </footer>

    <!-- Filters modal -->
    <ShopFilterModal
      :open="isFilterOpen"
      :min-rating="minRating"
      :sort-by="sortBy"
      :min-price="minPrice"
      :max-price="maxPrice"
      :result-count="filteredVisibleShops.length"
      @close="isFilterOpen = false"
      @update:min-rating="minRating = $event"
      @update:sort-by="sortBy = $event"
      @update:min-price="minPrice = $event"
      @update:max-price="maxPrice = $event"
      @clear="clearFilters"
    />
  </CustomerLayout>
</template>

<style>
/* Leaflet divIcon markup and popup content live outside Vue's scoped style
   boundary, so this block is intentionally global. */

/* --- Pin markers --- */
.pin-marker {
  background: transparent;
  border: none;
}

.pin-marker__bubble {
  width: 44px;
  height: 44px;
  border-radius: 9999px;
  background: #fff;
  border: 2px solid #fff;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.25);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  outline: 1px solid rgba(15, 23, 42, 0.12);
}

.pin-marker--barber .pin-marker__bubble {
  border-color: #0f172a;
  outline-color: rgba(15, 23, 42, 0.25);
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.3);
}

.pin-marker__bubble img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.pin-marker__initial {
  font-size: 16px;
  font-weight: 600;
  color: #0f172a;
  font-family: ui-sans-serif, system-ui, sans-serif;
  line-height: 1;
}

.pin-marker__tail {
  width: 10px;
  height: 10px;
  background: #fff;
  border-right: 2px solid #fff;
  border-bottom: 2px solid #fff;
  box-shadow: 2px 2px 4px rgba(15, 23, 42, 0.18);
  transform: rotate(45deg);
  margin: -6px auto 0;
}

.pin-marker--barber .pin-marker__tail {
  border-color: #0f172a;
}

/* --- Map popup card --- */
.leaflet-popup-content-wrapper {
  padding: 0 !important;
  border-radius: 12px !important;
  overflow: hidden;
  box-shadow: 0 12px 28px rgba(15, 23, 42, 0.18), 0 2px 6px rgba(15, 23, 42, 0.08) !important;
  border: 1px solid rgb(226 232 240);
}
.leaflet-popup-content {
  margin: 0 !important;
  width: 240px !important;
  line-height: 1.35;
}
.leaflet-popup-tip {
  background: #fff;
  border: 1px solid rgb(226 232 240);
}
.leaflet-popup-close-button {
  color: rgba(15, 23, 42, 0.55) !important;
  font-size: 22px !important;
  padding: 6px 8px !important;
  top: 4px !important;
  right: 4px !important;
}
.leaflet-popup-close-button:hover {
  color: #0f172a !important;
}

.ibook-popup {
  background: #fff;
  font-family: ui-sans-serif, system-ui, sans-serif;
  color: #0f172a;
}
.ibook-popup__media {
  position: relative;
  aspect-ratio: 4 / 3;
  background: rgb(241 245 249);
  overflow: hidden;
}
.ibook-popup__media-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgb(203 213 225);
}
.ibook-popup__chip {
  position: absolute;
  top: 10px;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 9px;
  border-radius: 6px;
  background: #fff;
  color: rgb(51 65 85);
  font-size: 12.5px;
  font-weight: 600;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.12);
}
.ibook-popup__chip--left { left: 10px; }
.ibook-popup__chip--right { right: 10px; color: #0f172a; }

.ibook-popup__body {
  padding: 14px 14px 14px;
}
.ibook-popup__title {
  font-size: 15px;
  font-weight: 600;
  letter-spacing: -0.01em;
  line-height: 1.25;
  margin: 0 0 6px;
  color: #0f172a;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}
.ibook-popup__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: rgb(100 116 139);
  margin: 0 0 12px;
  overflow: hidden;
}
.ibook-popup__meta .truncate {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ibook-popup__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding-top: 10px;
  border-top: 1px solid rgb(241 245 249);
}
.ibook-popup__cta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  background: #0f172a;
  color: #fff !important;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none !important;
  transition: background-color 0.15s ease;
}
.ibook-popup__cta:hover {
  background: #1e293b;
}
</style>
