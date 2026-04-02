<script setup lang="ts">
import { ref, computed, toRaw, onMounted } from 'vue'
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
import ShopFilterBar from '@/components/discovery/ShopFilterBar.vue'
import type { ShopListItem } from '@/components/discovery/ShopCard.vue'
import api from '@/lib/axios'

// ---- Geolocation (Pattern 2 from RESEARCH.md) ----
const TASHKENT: [number, number] = [41.2995, 69.2401]
const center = ref<[number, number]>(TASHKENT)
const locationDenied = ref(false)
const lat = ref<number | null>(null)
const lng = ref<number | null>(null)

onMounted(() => {
  if (!navigator.geolocation) {
    locationDenied.value = true
    return
  }
  navigator.geolocation.getCurrentPosition(
    (pos) => {
      lat.value = pos.coords.latitude
      lng.value = pos.coords.longitude
      center.value = [pos.coords.latitude, pos.coords.longitude]
    },
    () => {
      locationDenied.value = true
      center.value = TASHKENT
    },
    { timeout: 5000 },
  )
})

// ---- Filter state ----
const searchName = ref('')
const minRating = ref(0)
const sortBy = ref('distance')
const minPrice = ref<number | null>(null)
const maxPrice = ref<number | null>(null)

// Debounced name search — 400ms
const debouncedName = ref('')
const setDebouncedName = useDebounceFn((v: string) => {
  debouncedName.value = v
}, 400)

function onSearchUpdate(v: string) {
  searchName.value = v
  setDebouncedName(v)
}

// ---- Data fetching (Pattern 4 from RESEARCH.md) ----
const { data: rawShops, isLoading } = useQuery({
  queryKey: computed(() => ['shops', lat.value, lng.value, debouncedName.value, minRating.value]),
  queryFn: async () => {
    const params: Record<string, string | number> = {}
    if (lat.value !== null) params.lat = lat.value
    if (lng.value !== null) params.lng = lng.value
    if (debouncedName.value) params.name = debouncedName.value
    if (minRating.value > 0) params.min_rating = minRating.value
    const res = await api.get('/api/shops/', { params })
    return res.data as ShopListItem[]
  },
})

const shops = computed(() => rawShops.value ?? [])

// Shops that have coordinates (for map pins)
const shopsWithCoords = computed(() =>
  shops.value.filter((s): s is ShopListItem & { lat: number; lng: number } =>
    s.lat !== null && s.lng !== null,
  ),
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
      .filter((s) => bounds.contains([s.lat, s.lng]))
      .map((s) => s.id),
  )
}

function onMapReady() {
  updateVisibleShops()
}

function onMoveEnd() {
  updateVisibleShops()
}

// Shops visible in current map viewport (before additional client-side filters)
const visibleShops = computed(() => {
  // If no viewport tracking yet (no location or map not ready), show all shops
  if (visibleShopIds.value.size === 0 && shopsWithCoords.value.length === 0) {
    return shops.value
  }
  if (visibleShopIds.value.size === 0) {
    // Map not ready yet — show all
    return shops.value
  }
  return shops.value.filter((s) => {
    if (s.lat === null || s.lng === null) return false
    return visibleShopIds.value.has(s.id)
  })
})

// ---- filteredVisibleShops: apply all client-side filters ----
const filteredVisibleShops = computed(() => {
  let result = visibleShops.value

  // 1. Rating filter (Phase 5: avg_rating is always null until reviews added)
  if (minRating.value > 0) {
    result = result.filter(
      (s) => s.avg_rating !== null && s.avg_rating >= minRating.value,
    )
  }

  // 2. Min price filter
  if (minPrice.value !== null) {
    result = result.filter(
      (s) => s.min_price !== null && s.min_price >= (minPrice.value as number),
    )
  }

  // 3. Max price filter
  if (maxPrice.value !== null) {
    result = result.filter(
      (s) => s.min_price !== null && s.min_price <= (maxPrice.value as number),
    )
  }

  // 4. Sort
  if (sortBy.value === 'name') {
    result = [...result].sort((a, b) => a.name.localeCompare(b.name))
  }
  // 'distance': API returns shops ordered by distance when lat/lng provided; keep that order

  return result
})
</script>

<template>
  <CustomerLayout>
    <div class="max-w-7xl mx-auto px-4 md:px-8 py-4 md:py-6">
      <!-- Page header -->
      <div class="mb-4 md:mb-5">
        <h1 class="text-xl md:text-3xl font-bold text-ibook-brown-900">Explore Barbers</h1>
        <p class="mt-1 text-ibook-brown-500">Find and book the perfect barber near you.</p>
      </div>

      <!-- Location denied banner -->
      <div
        v-if="locationDenied"
        class="mb-4 flex items-center gap-3 rounded-xl bg-amber-50 border border-amber-200 px-4 py-3"
      >
        <svg
          class="h-5 w-5 text-amber-500 flex-shrink-0"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
          />
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <p class="text-sm text-amber-700">
          <span class="font-medium">Enable location for nearby results.</span>
          Showing Tashkent as default location.
        </p>
      </div>

      <!-- Map -->
      <div class="mb-4 rounded-xl overflow-hidden shadow-sm border border-ibook-brown-100 z-0">
        <LMap
          ref="mapRef"
          :zoom="13"
          :center="center"
          :use-global-leaflet="true"
          style="height: 50vh"
          class="z-0 md:h-[40vh]"
          @moveend="onMoveEnd"
          @ready="onMapReady"
        >
          <LTileLayer
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors"
          />
          <LMarkerClusterGroup>
            <LMarker
              v-for="shop in shopsWithCoords"
              :key="shop.id"
              :lat-lng="[shop.lat, shop.lng]"
            >
              <LPopup>
                <div class="min-w-[180px]">
                  <!-- Shop photo in popup -->
                  <div class="w-full h-20 bg-ibook-brown-100 rounded-lg overflow-hidden mb-2">
                    <img
                      v-if="shop.photo"
                      :src="shop.photo"
                      :alt="shop.name"
                      class="w-full h-full object-cover"
                    />
                    <div v-else class="w-full h-full flex items-center justify-center">
                      <svg
                        class="h-8 w-8 text-ibook-brown-300"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          stroke-width="1.5"
                          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16"
                        />
                      </svg>
                    </div>
                  </div>
                  <!-- Name -->
                  <p class="font-semibold text-ibook-brown-900 text-sm leading-snug mb-1">
                    {{ shop.name }}
                  </p>
                  <!-- Rating placeholder -->
                  <p class="text-xs text-ibook-brown-400 mb-2">
                    {{
                      shop.avg_rating !== null
                        ? `${shop.avg_rating.toFixed(1)} stars`
                        : 'No ratings yet'
                    }}
                  </p>
                  <!-- View button -->
                  <RouterLink
                    :to="{ name: 'customer-shop-detail', params: { shopId: shop.id } }"
                    class="block w-full py-1.5 px-3 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white text-xs font-semibold rounded-lg transition-colors text-center"
                  >
                    View
                  </RouterLink>
                </div>
              </LPopup>
            </LMarker>
          </LMarkerClusterGroup>
        </LMap>
      </div>

      <!-- Filter bar -->
      <div class="mb-5 bg-white rounded-xl border border-ibook-brown-100 shadow-sm px-4 py-3">
        <ShopFilterBar
          :search="searchName"
          :min-rating="minRating"
          :sort-by="sortBy"
          :min-price="minPrice"
          :max-price="maxPrice"
          @update:search="onSearchUpdate"
          @update:min-rating="minRating = $event"
          @update:sort-by="sortBy = $event"
          @update:min-price="minPrice = $event"
          @update:max-price="maxPrice = $event"
        />
      </div>

      <!-- Shop card grid -->
      <div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <div
          v-for="n in 6"
          :key="n"
          class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm overflow-hidden"
        >
          <div class="h-40 bg-ibook-brown-100 animate-pulse" />
          <div class="p-4 space-y-3">
            <div class="h-4 bg-ibook-brown-100 rounded animate-pulse w-3/4" />
            <div class="h-3 bg-ibook-brown-50 rounded animate-pulse w-1/2" />
            <div class="h-8 bg-ibook-brown-100 rounded-lg animate-pulse" />
          </div>
        </div>
      </div>

      <div
        v-else-if="filteredVisibleShops.length === 0"
        class="flex flex-col items-center justify-center py-16 text-center"
      >
        <svg
          class="h-12 w-12 text-ibook-brown-300 mb-3"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="1.5"
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <p class="text-ibook-brown-500 font-medium">No barbershops found</p>
        <p class="text-ibook-brown-400 text-sm mt-1">Try adjusting your filters or panning the map.</p>
      </div>

      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        <ShopCard v-for="shop in filteredVisibleShops" :key="shop.id" :shop="shop" />
      </div>
    </div>
  </CustomerLayout>
</template>
