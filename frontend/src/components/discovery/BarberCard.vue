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
</script>

<template>
  <div
    class="bg-white rounded-xl border border-ibook-brown-100 shadow-sm hover:shadow-md transition-shadow p-4"
  >
    <div class="flex items-start gap-4">
      <!-- Avatar -->
      <div class="flex-shrink-0 w-16 h-16 rounded-full overflow-hidden bg-ibook-brown-100">
        <img
          v-if="props.barber.avatar"
          :src="props.barber.avatar"
          :alt="props.barber.full_name"
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
              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
            />
          </svg>
        </div>
      </div>

      <!-- Info -->
      <div class="flex-1 min-w-0">
        <h3 class="font-semibold text-ibook-brown-900 text-base leading-tight mb-2 truncate">
          {{ props.barber.full_name }}
        </h3>

        <!-- Top services chips -->
        <div v-if="props.barber.top_services.length > 0" class="flex flex-wrap gap-1.5 mb-3">
          <span
            v-for="service in props.barber.top_services.slice(0, 3)"
            :key="service.id"
            class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-ibook-brown-100 text-ibook-brown-700"
          >
            {{ service.name }} &middot; {{ formatPrice(service.price) }}
          </span>
        </div>
        <p v-else class="text-xs text-ibook-brown-400 mb-3">No services listed</p>

        <!-- Action buttons -->
        <div class="flex gap-2 flex-wrap">
          <RouterLink
            :to="{ name: 'customer-barber-profile', params: { barberId: props.barber.id } }"
            class="inline-flex items-center justify-center py-1.5 px-3 border border-ibook-brown-300 hover:bg-ibook-brown-50 text-ibook-brown-800 text-xs font-semibold rounded-lg transition-colors"
          >
            View Profile
          </RouterLink>
          <RouterLink
            :to="{ name: 'customer-booking', params: { barberId: props.barber.id } }"
            class="inline-flex items-center justify-center py-1.5 px-3 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white text-xs font-semibold rounded-lg transition-colors"
          >
            Book
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>
