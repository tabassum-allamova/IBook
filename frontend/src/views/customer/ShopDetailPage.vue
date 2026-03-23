<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
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

const route = useRoute()
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

interface BarberMemberEntry {
  id: number
  barber: {
    id: number
    full_name: string
    email: string
    avatar: string | null
    top_services: Array<{ id: number; name: string; price: number }>
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

// JS getDay() returns 0=Sunday; our model uses 0=Monday
const todayIndex = computed(() => {
  const jsDay = new Date().getDay()
  return (jsDay + 6) % 7 // convert to Monday=0
})

function formatTime(t: string | null): string {
  if (!t) return ''
  // Strip seconds: "HH:MM:SS" -> "HH:MM"
  return t.slice(0, 5)
}

function getHoursForDay(dayIndex: number): HoursEntry | undefined {
  return shop.value?.hours.find((h) => h.day_of_week === dayIndex)
}

const mapCenter = computed<[number, number] | null>(() => {
  if (shop.value?.lat && shop.value?.lng) {
    return [shop.value.lat, shop.value.lng]
  }
  return null
})

// Scroll to current gallery photo
let galleryEl: HTMLElement | null = null

const fromShop = computed(() => {
  return route.query.from === 'shop'
})
</script>

<template>
  <CustomerLayout>
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

      <!-- Back link -->
      <RouterLink
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
        <div class="h-56 bg-ibook-brown-100 rounded-xl animate-pulse" />
        <div class="space-y-3">
          <div class="h-8 bg-ibook-brown-100 rounded animate-pulse w-1/2" />
          <div class="h-4 bg-ibook-brown-50 rounded animate-pulse w-1/3" />
        </div>
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
        <p class="text-ibook-brown-700 font-semibold text-lg">Shop not found</p>
        <p class="text-ibook-brown-400 text-sm mt-1">This shop may have been removed or the link is invalid.</p>
        <RouterLink
          to="/customer/explore"
          class="mt-4 inline-block py-2 px-4 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white text-sm font-semibold rounded-lg transition-colors"
        >
          Back to Explore
        </RouterLink>
      </div>

      <!-- Shop content -->
      <div v-else-if="shop" class="space-y-8">

        <!-- Photo gallery -->
        <div v-if="shop.photos.length > 0">
          <div
            class="flex gap-3 overflow-x-auto pb-2"
            style="scroll-snap-type: x mandatory; -webkit-overflow-scrolling: touch;"
          >
            <div
              v-for="photo in shop.photos.slice(0, 5)"
              :key="photo.id"
              class="flex-shrink-0 w-72 sm:w-80 h-52 rounded-xl overflow-hidden bg-ibook-brown-100"
              style="scroll-snap-align: start;"
            >
              <img
                :src="photo.image"
                :alt="shop.name"
                class="w-full h-full object-cover"
              />
            </div>
          </div>
        </div>
        <div
          v-else
          class="h-52 rounded-xl bg-ibook-brown-100 flex items-center justify-center"
        >
          <div class="text-center text-ibook-brown-400">
            <svg class="h-12 w-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p class="text-sm">No photos yet</p>
          </div>
        </div>

        <!-- Shop info -->
        <div>
          <h1 class="text-3xl font-bold text-ibook-brown-900 mb-1">{{ shop.name }}</h1>
          <p class="text-ibook-brown-500 flex items-center gap-1.5 mb-3">
            <svg class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            {{ shop.address }}
          </p>
          <p v-if="shop.description" class="text-ibook-brown-700 leading-relaxed">
            {{ shop.description }}
          </p>
        </div>

        <!-- Operating hours -->
        <div class="bg-white rounded-xl border border-ibook-brown-100 shadow-sm p-5">
          <h2 class="text-lg font-semibold text-ibook-brown-900 mb-4">Operating Hours</h2>
          <table class="w-full text-sm">
            <tbody>
              <tr
                v-for="(day, index) in DAYS"
                :key="index"
                :class="[
                  'border-b border-ibook-brown-50 last:border-0',
                  index === todayIndex ? 'bg-ibook-brown-50 rounded' : '',
                ]"
              >
                <td class="py-2 pr-4 font-medium text-ibook-brown-800 w-28">
                  <span v-if="index === todayIndex" class="inline-flex items-center gap-1.5">
                    {{ day }}
                    <span class="text-xs font-normal text-ibook-brown-500">(today)</span>
                  </span>
                  <span v-else>{{ day }}</span>
                </td>
                <td class="py-2 text-ibook-brown-600">
                  <template v-if="getHoursForDay(index)?.is_open">
                    {{ formatTime(getHoursForDay(index)?.opens_at ?? null) }} – {{ formatTime(getHoursForDay(index)?.closes_at ?? null) }}
                  </template>
                  <span v-else class="text-ibook-brown-400">Closed</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Barber cards -->
        <div>
          <h2 class="text-lg font-semibold text-ibook-brown-900 mb-4">Our Barbers</h2>
          <div v-if="shop.members.length > 0" class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <BarberCard
              v-for="member in shop.members"
              :key="member.id"
              :barber="member.barber"
              :shop-id="shop.id"
            />
          </div>
          <p v-else class="text-ibook-brown-400 text-sm">No barbers listed yet.</p>
        </div>

        <!-- Mini static map -->
        <div v-if="mapCenter" class="bg-white rounded-xl border border-ibook-brown-100 shadow-sm overflow-hidden">
          <h2 class="text-lg font-semibold text-ibook-brown-900 px-5 pt-5 pb-3">Location</h2>
          <LMap
            :zoom="15"
            :center="mapCenter"
            :use-global-leaflet="true"
            :dragging="false"
            :scroll-wheel-zoom="false"
            :zoom-control="false"
            :double-click-zoom="false"
            :attribution-control="false"
            style="height: 200px; width: 100%;"
          >
            <LTileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <LMarker :lat-lng="mapCenter" />
          </LMap>
        </div>

      </div>
    </div>
  </CustomerLayout>
</template>
