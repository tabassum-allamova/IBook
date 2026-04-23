<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery } from '@tanstack/vue-query'
import { useDebounceFn } from '@vueuse/core'
import CustomerLayout from '@/layouts/CustomerLayout.vue'
import ShopCard from '@/components/discovery/ShopCard.vue'
import ShopFilterModal from '@/components/discovery/ShopFilterModal.vue'
import type { ShopListItem } from '@/components/discovery/ShopCard.vue'
import api from '@/lib/axios'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()

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

// ---- URL-bound filters ----
function qStr(key: string): string {
  const v = route.query[key]
  return typeof v === 'string' ? v : ''
}
function qNum(key: string): number {
  const v = Number(route.query[key])
  return Number.isFinite(v) ? v : 0
}
function qNumOrNull(key: string): number | null {
  const raw = route.query[key]
  if (typeof raw !== 'string' || raw === '') return null
  const n = Number(raw)
  return Number.isFinite(n) ? n : null
}

function updateQuery(patch: Record<string, string | number | null | undefined>) {
  const next: Record<string, string> = {}
  for (const [k, v] of Object.entries(route.query)) {
    if (typeof v === 'string') next[k] = v
  }
  for (const [k, v] of Object.entries(patch)) {
    if (v === '' || v === null || v === undefined) delete next[k]
    else next[k] = String(v)
  }
  router.replace({ name: 'customer-search', query: next })
}

const q = computed(() => qStr('q'))
const region = computed(() => qStr('region'))
const minRating = computed(() => qNum('rating'))
const sortBy = computed(() => qStr('sort') || 'name')
const minPrice = computed(() => qNumOrNull('minPrice'))
const maxPrice = computed(() => qNumOrNull('maxPrice'))

// ---- Search input (debounced commits to URL) ----
const searchInput = ref(q.value)
const commitSearch = useDebounceFn((v: string) => {
  updateQuery({ q: v.trim() || null })
}, 350)

function onSearchInput(e: Event) {
  const v = (e.target as HTMLInputElement).value
  searchInput.value = v
  commitSearch(v)
}

function clearSearch() {
  searchInput.value = ''
  updateQuery({ q: null })
}

// ---- Filter modal ----
const isFilterOpen = ref(false)

const activeFilterCount = computed(() => {
  let n = 0
  if (minRating.value > 0) n++
  if (minPrice.value !== null) n++
  if (maxPrice.value !== null) n++
  if (sortBy.value && sortBy.value !== 'name') n++
  return n
})

function clearAllFilters() {
  router.replace({ name: 'customer-search', query: {} })
  searchInput.value = ''
}

// ---- Data ----
const { data: rawShops, isLoading: shopsLoading } = useQuery({
  queryKey: computed(() => ['search-shops', q.value, minRating.value]),
  queryFn: async () => {
    const params: Record<string, string | number> = {}
    if (q.value) params.name = q.value
    if (minRating.value > 0) params.min_rating = minRating.value
    const res = await api.get('/api/shops/', { params })
    return res.data as ShopListItem[]
  },
})

interface SoloBarber {
  id: number
  full_name: string
  avatar: string | null
  years_of_experience: number | null
  min_price: number | null
  avg_rating: number | null
  top_service_names: string[]
}

const { data: rawBarbers, isLoading: barbersLoading } = useQuery<SoloBarber[]>({
  queryKey: computed(() => ['search-barbers', q.value]),
  queryFn: async () => {
    const params: Record<string, string> = { solo: 'true' }
    if (q.value) params.name = q.value
    const res = await api.get<SoloBarber[]>('/api/barbers/', { params })
    return res.data
  },
})

// ---- Client-side filtering ----
function priceInRange(price: number | null): boolean {
  if (price === null) return minPrice.value === null && maxPrice.value === null
  if (minPrice.value !== null && price < minPrice.value) return false
  if (maxPrice.value !== null && price > maxPrice.value) return false
  return true
}

const filteredShops = computed(() => {
  let result = rawShops.value ?? []

  if (region.value) {
    const r = REGIONS.find((x) => x.label === region.value)
    if (r) {
      result = result.filter((s) => {
        const addr = (s.address ?? '').toLowerCase()
        return r.aliases.some((a) => addr.includes(a))
      })
    }
  }
  if (minPrice.value !== null || maxPrice.value !== null) {
    result = result.filter((s) => priceInRange(s.min_price))
  }
  if (sortBy.value === 'name') {
    result = [...result].sort((a, b) => a.name.localeCompare(b.name))
  }
  return result
})

const filteredBarbers = computed(() => {
  let result = rawBarbers.value ?? []

  // Region doesn't apply to solo barbers — they don't have a bound address.
  // Rating
  if (minRating.value > 0) {
    result = result.filter((b) => b.avg_rating !== null && b.avg_rating >= minRating.value)
  }
  if (minPrice.value !== null || maxPrice.value !== null) {
    result = result.filter((b) => priceInRange(b.min_price))
  }
  if (sortBy.value === 'name') {
    result = [...result].sort((a, b) => a.full_name.localeCompare(b.full_name))
  }
  return result
})

function formatPrice(amount: number): string {
  return new Intl.NumberFormat('en-US').format(amount) + ' UZS'
}

const isLoading = computed(() => shopsLoading.value || barbersLoading.value)
const totalCount = computed(() => filteredShops.value.length + filteredBarbers.value.length)
</script>

<template>
  <CustomerLayout>
    <!-- Toolbar -->
    <section class="bg-white sticky top-16 z-30 border-b border-slate-200">
      <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-4 flex items-center gap-3">
        <!-- Search -->
        <label class="relative flex-1 min-w-0">
          <span class="sr-only">{{ t('search.searchShopsBarbersLabel') }}</span>
          <svg
            class="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <input
            type="text"
            :value="searchInput"
            :placeholder="t('search.searchShopsBarbers')"
            class="w-full h-10 pl-10 pr-9 text-sm bg-white border border-slate-200 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition"
            @input="onSearchInput"
          />
          <button
            v-if="searchInput"
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

        <!-- Region -->
        <label class="relative flex-shrink-0">
          <span class="sr-only">{{ t('search.regionLabel') }}</span>
          <select
            :value="region"
            class="appearance-none h-10 pl-3 pr-8 text-sm bg-white border border-slate-200 rounded-lg text-slate-900 hover:border-slate-400 focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition cursor-pointer w-32 md:w-44"
            @change="(e) => updateQuery({ region: (e.target as HTMLSelectElement).value || null })"
          >
            <option value="">{{ t('search.allRegions') }}</option>
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
            class="inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 text-sm font-semibold rounded-full bg-white text-slate-900"
          >
            {{ activeFilterCount }}
          </span>
        </button>
      </div>
    </section>

    <!-- Results header -->
    <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 pt-6 md:pt-8">
      <div class="flex items-baseline justify-between gap-3">
        <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          <template v-if="q">{{ t('search.resultsFor', { q }) }}</template>
          <template v-else>{{ t('search.title') }}</template>
        </h1>
        <button
          v-if="activeFilterCount > 0 || q || region"
          type="button"
          class="text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors"
          @click="clearAllFilters"
        >
          {{ t('search.clearAll') }}
        </button>
      </div>
      <p class="mt-1 text-sm text-slate-600">
        <template v-if="isLoading">{{ t('search.searching') }}</template>
        <template v-else-if="totalCount === 0">{{ t('search.noMatches') }}</template>
        <template v-else>
          {{ t('search.summaryShops', { count: filteredShops.length }, filteredShops.length) }}
          ·
          {{ t('search.summaryBarbers', { count: filteredBarbers.length }, filteredBarbers.length) }}
        </template>
      </p>
    </section>

    <!-- Content -->
    <section class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-8 md:py-10 space-y-12 md:space-y-14">
      <!-- Loading -->
      <div v-if="isLoading" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
        <div v-for="n in 6" :key="n" class="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div class="aspect-[4/3] bg-slate-100 animate-pulse" />
          <div class="p-5 space-y-3">
            <div class="h-5 bg-slate-100 animate-pulse rounded w-3/4" />
            <div class="h-4 bg-slate-100 animate-pulse rounded w-1/2" />
            <div class="h-10 bg-slate-100 animate-pulse rounded" />
          </div>
        </div>
      </div>

      <!-- Empty -->
      <div
        v-else-if="totalCount === 0"
        class="bg-white rounded-xl border border-slate-200 py-16 px-6 text-center"
      >
        <svg class="h-10 w-10 text-slate-300 mx-auto mb-3" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <p class="text-lg font-semibold text-slate-900 mb-1">{{ t('search.nothingMatches') }}</p>
        <p class="text-sm text-slate-500 mb-5">{{ t('search.tryBroadening') }}</p>
        <button
          type="button"
          class="inline-flex items-center gap-1.5 h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:border-slate-400 hover:text-slate-900 transition-colors"
          @click="clearAllFilters"
        >
          {{ t('search.clearAllFilters') }}
        </button>
      </div>

      <!-- Results -->
      <template v-else>
        <!-- Shops -->
        <div v-if="filteredShops.length > 0">
          <div class="flex items-baseline justify-between gap-3 mb-5 md:mb-6">
            <h2 class="text-lg md:text-xl font-semibold text-slate-900 tracking-tight">
              {{ t('search.shops') }}
              <span class="ml-2 text-sm font-medium text-slate-500">{{ filteredShops.length }}</span>
            </h2>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
            <ShopCard v-for="shop in filteredShops" :key="shop.id" :shop="shop" />
          </div>
        </div>

        <!-- Solo barbers -->
        <div v-if="filteredBarbers.length > 0">
          <div class="flex items-baseline justify-between gap-3 mb-5 md:mb-6">
            <h2 class="text-lg md:text-xl font-semibold text-slate-900 tracking-tight">
              {{ t('search.soloBarbers') }}
              <span class="ml-2 text-sm font-medium text-slate-500">{{ filteredBarbers.length }}</span>
            </h2>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
            <RouterLink
              v-for="b in filteredBarbers"
              :key="b.id"
              :to="{ name: 'customer-barber-profile', params: { barberId: b.id } }"
              class="group block bg-white rounded-xl border border-slate-200 hover:border-slate-300 hover:shadow-md transition-all overflow-hidden focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
            >
              <div class="relative aspect-[4/3] overflow-hidden bg-slate-100">
                <img
                  v-if="b.avatar"
                  :src="b.avatar"
                  :alt="b.full_name"
                  class="w-full h-full object-cover transition-transform duration-500 ease-out group-hover:scale-[1.03]"
                  loading="lazy"
                />
                <div v-else class="w-full h-full flex items-center justify-center">
                  <svg class="h-14 w-14 text-slate-300" fill="none" stroke="currentColor" stroke-width="1.2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                </div>
                <span class="absolute top-3 left-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-sm font-semibold bg-white text-slate-700 shadow-sm">
                  <span class="h-1.5 w-1.5 rounded-full bg-slate-900"></span>
                  {{ t('search.solo') }}
                </span>
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
              <div class="p-5">
                <h3 class="text-lg font-semibold text-slate-900 mb-1 line-clamp-1 tracking-tight">
                  {{ b.full_name }}
                </h3>
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
                      {{ b.years_of_experience }} {{ t('search.yearsShort', b.years_of_experience) }} {{ t('search.yearsExperience') }}
                    </template>
                    <template v-else>
                      {{ t('search.servicesOnArrival') }}
                    </template>
                  </span>
                </p>
                <div class="flex items-center justify-between pt-3 border-t border-slate-100">
                  <div class="min-w-0">
                    <p class="text-sm font-medium uppercase tracking-wide text-slate-400">{{ t('explore.from') }}</p>
                    <p v-if="b.min_price !== null" class="text-base font-semibold text-slate-900">
                      {{ formatPrice(b.min_price) }}
                    </p>
                    <p v-else class="text-sm text-slate-400">{{ t('search.onArrival') }}</p>
                  </div>
                  <span class="inline-flex items-center gap-1 text-sm font-semibold text-slate-900 group-hover:gap-1.5 transition-all">
                    {{ t('search.view') }}
                    <svg class="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
                    </svg>
                  </span>
                </div>
              </div>
            </RouterLink>
          </div>
        </div>
      </template>
    </section>

    <!-- Filter modal (URL-bound; updates fire replace()) -->
    <ShopFilterModal
      :open="isFilterOpen"
      :min-rating="minRating"
      :sort-by="sortBy"
      :min-price="minPrice"
      :max-price="maxPrice"
      :result-count="totalCount"
      @close="isFilterOpen = false"
      @update:min-rating="(v) => updateQuery({ rating: v > 0 ? v : null })"
      @update:sort-by="(v) => updateQuery({ sort: v })"
      @update:min-price="(v) => updateQuery({ minPrice: v })"
      @update:max-price="(v) => updateQuery({ maxPrice: v })"
      @clear="() => updateQuery({ rating: null, sort: null, minPrice: null, maxPrice: null })"
    />
  </CustomerLayout>
</template>
