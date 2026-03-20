<script setup lang="ts">
import { RouterLink } from 'vue-router'

export interface ShopListItem {
  id: number
  name: string
  address: string
  lat: number | null
  lng: number | null
  photo: string | null
  distance_km: number | null
  is_open_now: boolean
  min_price: number | null
  avg_rating: number | null
}

const props = defineProps<{
  shop: ShopListItem
}>()

function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-US').format(amount) + ' UZS'
}

function formatDistance(km: number | null): string {
  if (km === null) return 'N/A'
  return `${km.toFixed(1)} km`
}
</script>

<template>
  <div
    class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm hover:shadow-md transition-shadow overflow-hidden flex flex-col"
  >
    <!-- Photo -->
    <div class="h-40 bg-ibook-brown-100 overflow-hidden flex-shrink-0">
      <img
        v-if="props.shop.photo"
        :src="props.shop.photo"
        :alt="props.shop.name"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-14 w-14 text-ibook-brown-300"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-2 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
          />
        </svg>
      </div>
    </div>

    <!-- Content -->
    <div class="p-4 flex flex-col flex-1">
      <!-- Name -->
      <h3 class="font-semibold text-ibook-brown-900 text-base leading-snug mb-2 line-clamp-1">
        {{ props.shop.name }}
      </h3>

      <!-- Badges row -->
      <div class="flex flex-wrap gap-1.5 mb-3">
        <!-- Open/Closed badge -->
        <span
          :class="[
            'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium',
            props.shop.is_open_now
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-700',
          ]"
        >
          {{ props.shop.is_open_now ? 'Open' : 'Closed' }}
        </span>

        <!-- Distance badge -->
        <span
          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ibook-brown-100 text-ibook-brown-700"
        >
          {{ formatDistance(props.shop.distance_km) }}
        </span>

        <!-- Rating badge -->
        <span
          v-if="props.shop.avg_rating !== null"
          class="inline-flex items-center gap-0.5 px-2 py-0.5 rounded-full text-xs font-medium bg-ibook-gold-100 text-ibook-gold-800"
        >
          <svg class="h-3 w-3" fill="currentColor" viewBox="0 0 20 20">
            <path
              d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"
            />
          </svg>
          {{ props.shop.avg_rating.toFixed(1) }}
        </span>
        <span
          v-else
          class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ibook-brown-50 text-ibook-brown-400"
        >
          No ratings yet
        </span>
      </div>

      <!-- Price -->
      <p class="text-sm text-ibook-brown-600 mb-4 flex-1">
        <span v-if="props.shop.min_price !== null">
          from {{ formatPrice(props.shop.min_price) }}
        </span>
        <span v-else class="text-ibook-brown-400">No services listed</span>
      </p>

      <!-- View button -->
      <RouterLink
        :to="{ name: 'customer-shop-detail', params: { shopId: props.shop.id } }"
        class="block w-full py-2 px-4 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white text-sm font-semibold rounded-lg transition-colors text-center"
      >
        View
      </RouterLink>
    </div>
  </div>
</template>
