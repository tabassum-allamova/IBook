<script setup lang="ts">
import { RouterLink } from 'vue-router'

interface TopService {
  id: number
  name: string
  price: number
}

export interface BarberMember {
  id: number
  full_name: string
  email: string
  avatar: string | null
  top_services: TopService[]
}

const props = defineProps<{
  barber: BarberMember
  shopId: number
}>()

function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-US').format(amount) + ' UZS'
}

function minPrice(services: TopService[]): number | null {
  if (!services.length) return null
  return services.reduce((m, s) => (s.price < m ? s.price : m), services[0].price)
}
</script>

<template>
  <article
    class="bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-sm transition-all p-4 flex gap-3.5 items-start"
  >
    <!-- Avatar -->
    <div class="flex-shrink-0 w-12 h-12 rounded-full overflow-hidden bg-slate-100 border border-slate-200">
      <img
        v-if="props.barber.avatar"
        :src="props.barber.avatar"
        :alt="props.barber.full_name"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center">
        <svg class="h-6 w-6 text-slate-300" fill="none" stroke="currentColor" stroke-width="1.3" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
        </svg>
      </div>
    </div>

    <!-- Content -->
    <div class="flex-1 min-w-0 flex flex-col">
      <!-- Name -->
      <h3 class="text-[15px] font-semibold text-slate-900 mb-1 truncate tracking-tight">
        {{ props.barber.full_name }}
      </h3>

      <!-- Top services -->
      <div v-if="props.barber.top_services.length > 0" class="flex flex-wrap gap-1 mb-2">
        <span
          v-for="service in props.barber.top_services.slice(0, 3)"
          :key="service.id"
          class="inline-flex items-center px-2 py-0.5 rounded text-sm font-medium bg-slate-100 text-slate-700"
        >
          {{ service.name }}
        </span>
      </div>
      <p v-else class="text-sm text-slate-400 mb-2">
        Services on arrival
      </p>

      <!-- From price -->
      <p v-if="minPrice(props.barber.top_services) !== null" class="text-sm text-slate-600 mb-3">
        <span class="text-slate-400">From</span>
        <span class="ml-1 font-semibold text-slate-900">
          {{ formatPrice(minPrice(props.barber.top_services) as number) }}
        </span>
      </p>

      <!-- Actions -->
      <div class="mt-auto flex items-center gap-3">
        <RouterLink
          :to="{ name: 'customer-barber-profile', params: { barberId: props.barber.id }, query: { shopId: props.shopId } }"
          class="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
        >
          View profile
        </RouterLink>
        <RouterLink
          :to="{ name: 'customer-booking', params: { barberId: props.barber.id } }"
          class="ml-auto inline-flex items-center gap-1 px-3 h-8 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
        >
          Book
          <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </RouterLink>
      </div>
    </div>
  </article>
</template>
