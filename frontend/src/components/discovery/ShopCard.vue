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

const props = withDefaults(
  defineProps<{
    shop: ShopListItem
    index?: number
  }>(),
  { index: 0 },
)

function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-US').format(amount) + ' UZS'
}

function formatDistance(km: number | null): string {
  if (km === null) return ''
  if (km < 1) return `${Math.round(km * 1000)} m away`
  return `${km.toFixed(1)} km away`
}
</script>

<template>
  <RouterLink
    :to="{ name: 'customer-shop-detail', params: { shopId: props.shop.id } }"
    class="group block bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all overflow-hidden focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
  >
    <!-- Photo -->
    <div class="relative aspect-[4/3] overflow-hidden bg-slate-100">
      <img
        v-if="props.shop.photo"
        :src="props.shop.photo"
        :alt="props.shop.name"
        class="w-full h-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.03]"
        loading="lazy"
      />
      <div v-else class="w-full h-full flex items-center justify-center">
        <svg
          class="h-12 w-12 text-slate-300"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="1.2"
        >
          <circle cx="6" cy="6" r="3" />
          <circle cx="6" cy="18" r="3" />
          <path stroke-linecap="round" d="M20 4 L8.5 8 M20 20 L8.5 16 M14 12 L20 12" />
        </svg>
      </div>

      <!-- Open / Closed chip -->
      <span
        :class="[
          'absolute top-3 left-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold shadow-sm',
          props.shop.is_open_now
            ? 'bg-emerald-500 text-white'
            : 'bg-white text-slate-700',
        ]"
      >
        <span
          class="h-1.5 w-1.5 rounded-full"
          :class="props.shop.is_open_now ? 'bg-white' : 'bg-slate-400'"
        ></span>
        {{ props.shop.is_open_now ? 'Open now' : 'Closed' }}
      </span>

      <!-- Rating chip -->
      <span
        v-if="props.shop.avg_rating !== null"
        class="absolute top-3 right-3 inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold bg-white text-slate-900 shadow-sm"
      >
        <svg class="h-3 w-3 text-amber-400 fill-current" viewBox="0 0 20 20">
          <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
        </svg>
        {{ props.shop.avg_rating.toFixed(1) }}
      </span>
    </div>

    <!-- Content -->
    <div class="p-5">
      <h3 class="text-lg font-semibold text-slate-900 mb-1 line-clamp-1 tracking-tight">
        {{ props.shop.name }}
      </h3>

      <!-- Address / distance -->
      <p class="flex items-center gap-1.5 text-sm text-slate-500 mb-4 line-clamp-1">
        <svg class="h-3.5 w-3.5 flex-shrink-0 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.7" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
        <span class="truncate">
          {{ props.shop.distance_km !== null ? formatDistance(props.shop.distance_km) : props.shop.address }}
        </span>
      </p>

      <!-- Footer: price + CTA -->
      <div class="flex items-center justify-between pt-3 border-t border-slate-100">
        <div class="min-w-0">
          <p class="text-[11px] font-medium uppercase tracking-wide text-slate-400">From</p>
          <p v-if="props.shop.min_price !== null" class="text-base font-semibold text-slate-900">
            {{ formatPrice(props.shop.min_price) }}
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
</template>
