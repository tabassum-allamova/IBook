<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import api from '@/lib/axios'

const toast = useToast()

const router = useRouter()
const queryClient = useQueryClient()

// ── Types ─────────────────────────────────────────────────────────────────────

interface ShopHours {
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

interface ServiceSummary {
  id: number
  name: string
  price: number
}

interface BarberSummary {
  id: number
  full_name: string
  email: string
  avatar: string | null
  top_services: ServiceSummary[]
}

interface Member {
  id: number
  barber: BarberSummary
  added_at: string
}

interface Shop {
  id: number
  name: string
  address: string
  lat: string | null
  lng: string | null
  description: string
  hours: ShopHours[]
  photos: ShopPhoto[]
  members: Member[]
  created_at: string
}

// ── Data fetching ─────────────────────────────────────────────────────────────

const { data: shop, isPending: shopLoading, error: shopError } = useQuery<Shop>({
  queryKey: ['shop', 'owner'],
  queryFn: () => api.get('/api/shops/my/').then((r) => r.data),
  retry: false,
})

watch(shopError, (err: unknown) => {
  const e = err as { response?: { status?: number } } | null
  if (e?.response?.status === 404) {
    router.push('/owner/shop/setup')
  }
})

// ── Hours logic ───────────────────────────────────────────────────────────────

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

const isOpenNow = computed(() => {
  if (!shop.value) return false
  const now = new Date()
  const dayIndex = (now.getDay() + 6) % 7 // Convert JS Sunday=0 to Mon=0
  const todayHours = shop.value.hours.find((h) => h.day_of_week === dayIndex)
  if (!todayHours || !todayHours.is_open || !todayHours.opens_at || !todayHours.closes_at)
    return false

  const [openH, openM] = todayHours.opens_at.split(':').map(Number)
  const [closeH, closeM] = todayHours.closes_at.split(':').map(Number)
  const currentMinutes = now.getHours() * 60 + now.getMinutes()
  const openMinutes = openH * 60 + openM
  const closeMinutes = closeH * 60 + closeM

  // Check if in break
  if (todayHours.break_start && todayHours.break_end) {
    const [breakStartH, breakStartM] = todayHours.break_start.split(':').map(Number)
    const [breakEndH, breakEndM] = todayHours.break_end.split(':').map(Number)
    const breakStartMinutes = breakStartH * 60 + breakStartM
    const breakEndMinutes = breakEndH * 60 + breakEndM
    if (currentMinutes >= breakStartMinutes && currentMinutes < breakEndMinutes) return false
  }

  return currentMinutes >= openMinutes && currentMinutes < closeMinutes
})

const scheduleExpanded = ref(false)

// ── Add barber ────────────────────────────────────────────────────────────────

const barberIdInput = ref('')
const addBarberError = ref<string | null>(null)

const addBarber = useMutation({
  mutationFn: (barberId: number) =>
    api.post(`/api/shops/${shop.value!.id}/members/`, { barber_id: barberId }),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['shop', 'owner'] })
    barberIdInput.value = ''
    addBarberError.value = null
    toast.success('Barber added to shop')
  },
  onError: (err: unknown) => {
    const e = err as { response?: { data?: { detail?: string } } }
    addBarberError.value = e?.response?.data?.detail ?? 'Failed to add barber'
    toast.error(addBarberError.value ?? 'Failed to add barber')
  },
})

function handleAddBarber() {
  const id = parseInt(barberIdInput.value.trim(), 10)
  if (!id || isNaN(id)) {
    addBarberError.value = 'Please enter a valid barber ID'
    return
  }
  addBarberError.value = null
  addBarber.mutate(id)
}

// ── Remove barber ─────────────────────────────────────────────────────────────

const removeBarber = useMutation({
  mutationFn: (barberId: number) =>
    api.delete(`/api/shops/${shop.value!.id}/members/${barberId}/`),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['shop', 'owner'] })
    toast.success('Barber removed from shop')
  },
  onError: () => {
    toast.error('Failed to remove barber.')
  },
})

// ── Initials helper ───────────────────────────────────────────────────────────

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function formatPrice(price: number): string {
  return price.toLocaleString('uz-UZ') + ' UZS'
}
</script>

<template>
  <div class="min-h-screen bg-ibook-cream">
    <!-- Loading skeleton -->
    <div v-if="shopLoading" class="p-4 md:p-8 space-y-6">
      <div class="h-8 w-64 bg-ibook-brown-100 rounded animate-pulse" />
      <div class="h-4 w-48 bg-ibook-brown-100 rounded animate-pulse" />
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
        <div
          v-for="i in 3"
          :key="i"
          class="h-40 bg-ibook-brown-100 rounded-xl animate-pulse"
        />
      </div>
    </div>

    <!-- Shop content -->
    <div v-else-if="shop" class="p-4 md:p-8 space-y-8 max-w-5xl">
      <!-- Header -->
      <div>
        <h1 class="text-3xl font-bold text-ibook-brown-700">{{ shop.name }}</h1>
        <p class="text-ibook-brown-400 mt-1">{{ shop.address }}</p>
        <p v-if="shop.description" class="text-ibook-brown-400 mt-2 text-sm">
          {{ shop.description }}
        </p>
      </div>

      <!-- Hours section -->
      <div class="bg-white rounded-xl border border-ibook-brown-100 p-6">
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <h2 class="text-lg font-semibold text-ibook-brown-700">Hours</h2>
            <!-- Open/Closed badge -->
            <span
              class="px-2 py-0.5 rounded-full text-xs font-semibold"
              :class="isOpenNow ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'"
            >
              {{ isOpenNow ? 'Open now' : 'Closed' }}
            </span>
          </div>
          <button
            type="button"
            @click="scheduleExpanded = !scheduleExpanded"
            class="text-ibook-brown-400 hover:text-ibook-brown-700 transition-colors"
            :aria-label="scheduleExpanded ? 'Collapse schedule' : 'Expand schedule'"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-5 w-5 transition-transform"
              :class="scheduleExpanded ? 'rotate-180' : ''"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
            </svg>
          </button>
        </div>

        <!-- Full schedule (expandable) -->
        <div v-if="scheduleExpanded" class="mt-4 space-y-2">
          <div
            v-for="h in shop.hours"
            :key="h.day_of_week"
            class="flex items-center justify-between text-sm"
          >
            <span class="w-24 font-medium text-ibook-brown-700">{{ DAY_NAMES[h.day_of_week] }}</span>
            <span v-if="h.is_open && h.opens_at && h.closes_at" class="text-ibook-brown-400">
              {{ h.opens_at.slice(0, 5) }} – {{ h.closes_at.slice(0, 5) }}
              <span v-if="h.break_start && h.break_end" class="text-xs text-ibook-brown-400">
                (break {{ h.break_start.slice(0, 5) }}–{{ h.break_end.slice(0, 5) }})
              </span>
            </span>
            <span v-else class="text-ibook-brown-400">Closed</span>
          </div>
        </div>
      </div>

      <!-- Photos section -->
      <div v-if="shop.photos.length > 0" class="bg-white rounded-xl border border-ibook-brown-100 p-6">
        <h2 class="text-lg font-semibold text-ibook-brown-700 mb-4">Photos</h2>
        <div class="flex gap-3 overflow-x-auto pb-2">
          <img
            v-for="photo in shop.photos"
            :key="photo.id"
            :src="photo.image"
            :alt="shop.name + ' photo'"
            class="w-32 h-32 object-cover rounded-lg border border-ibook-brown-100 flex-shrink-0"
          />
        </div>
      </div>

      <!-- Barbers section -->
      <div class="bg-white rounded-xl border border-ibook-brown-100 p-6">
        <h2 class="text-lg font-semibold text-ibook-brown-700 mb-4">Barbers</h2>

        <!-- Add barber form -->
        <div class="flex gap-2 mb-6">
          <input
            v-model="barberIdInput"
            type="number"
            placeholder="Barber user ID"
            class="flex-1 px-3 py-2 border border-ibook-brown-200 rounded-lg bg-white text-ibook-brown-700 placeholder-ibook-brown-400 focus:outline-none focus:ring-2 focus:ring-ibook-gold-500 focus:border-transparent text-sm"
            @keyup.enter="handleAddBarber"
          />
          <button
            type="button"
            @click="handleAddBarber"
            :disabled="addBarber.isPending.value"
            class="px-4 py-2 bg-ibook-gold-500 hover:bg-ibook-gold-600 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ addBarber.isPending.value ? 'Adding...' : 'Add Barber' }}
          </button>
        </div>
        <p v-if="addBarberError" class="mb-4 text-sm text-red-500">{{ addBarberError }}</p>

        <!-- Barber cards grid -->
        <div
          v-if="shop.members.length > 0"
          class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          <div
            v-for="member in shop.members"
            :key="member.id"
            class="border border-ibook-brown-100 rounded-xl p-4 flex flex-col gap-3"
          >
            <!-- Barber header -->
            <div class="flex items-center gap-3">
              <!-- Avatar -->
              <div class="w-16 h-16 rounded-full overflow-hidden flex-shrink-0 bg-ibook-brown-100 flex items-center justify-center">
                <img
                  v-if="member.barber.avatar"
                  :src="member.barber.avatar"
                  :alt="member.barber.full_name"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-lg font-semibold text-ibook-brown-400">
                  {{ getInitials(member.barber.full_name) }}
                </span>
              </div>
              <!-- Name + role -->
              <div class="min-w-0">
                <p class="font-semibold text-ibook-brown-700 truncate">{{ member.barber.full_name }}</p>
                <span class="inline-block text-xs px-2 py-0.5 bg-ibook-gold-400 text-white rounded-full">
                  Barber
                </span>
              </div>
            </div>

            <!-- Top services -->
            <div v-if="member.barber.top_services.length > 0" class="space-y-1">
              <p
                v-for="service in member.barber.top_services"
                :key="service.id"
                class="text-xs text-ibook-brown-400"
              >
                {{ service.name }} — {{ formatPrice(service.price) }}
              </p>
            </div>
            <p v-else class="text-xs text-ibook-brown-400">No services listed</p>

            <!-- Remove button -->
            <button
              type="button"
              @click="removeBarber.mutate(member.barber.id)"
              :disabled="removeBarber.isPending.value"
              class="mt-auto self-start text-xs text-red-500 hover:text-red-600 font-medium transition-colors disabled:opacity-50"
            >
              Remove
            </button>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="py-8 text-center">
          <p class="text-ibook-brown-400 font-medium text-sm">No barbers yet</p>
          <p class="text-ibook-brown-300 text-xs mt-1">Enter a barber ID above to add your first barber.</p>
        </div>
      </div>
    </div>
  </div>
</template>
