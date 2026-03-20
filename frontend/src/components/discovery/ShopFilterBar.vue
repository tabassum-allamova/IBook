<script setup lang="ts">
const props = defineProps<{
  search: string
  minRating: number
  sortBy: string
  minPrice: number | null
  maxPrice: number | null
}>()

const emit = defineEmits<{
  (e: 'update:search', value: string): void
  (e: 'update:minRating', value: number): void
  (e: 'update:sortBy', value: string): void
  (e: 'update:minPrice', value: number | null): void
  (e: 'update:maxPrice', value: number | null): void
}>()

function onSearchInput(e: Event) {
  emit('update:search', (e.target as HTMLInputElement).value)
}

function onRatingChange(e: Event) {
  emit('update:minRating', Number((e.target as HTMLSelectElement).value))
}

function onSortChange(e: Event) {
  emit('update:sortBy', (e.target as HTMLSelectElement).value)
}

function onMinPriceInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  emit('update:minPrice', val === '' ? null : Number(val))
}

function onMaxPriceInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  emit('update:maxPrice', val === '' ? null : Number(val))
}
</script>

<template>
  <div class="flex flex-wrap gap-3 items-center">
    <!-- Name search -->
    <div class="relative flex-1 min-w-[160px]">
      <div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
        <svg
          class="h-4 w-4 text-ibook-brown-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
      </div>
      <input
        type="text"
        :value="props.search"
        placeholder="Search shops..."
        class="w-full pl-9 pr-3 py-2 text-sm rounded-lg border border-ibook-brown-200 bg-white text-ibook-brown-900 placeholder-ibook-brown-400 focus:outline-none focus:ring-2 focus:ring-ibook-brown-400"
        @input="onSearchInput"
      />
    </div>

    <!-- Rating filter -->
    <select
      :value="props.minRating"
      class="py-2 pl-3 pr-8 text-sm rounded-lg border border-ibook-brown-200 bg-white text-ibook-brown-700 focus:outline-none focus:ring-2 focus:ring-ibook-brown-400"
      @change="onRatingChange"
    >
      <option value="0">All ratings</option>
      <option value="1">1+ stars</option>
      <option value="2">2+ stars</option>
      <option value="3">3+ stars</option>
      <option value="4">4+ stars</option>
      <option value="5">5 stars</option>
    </select>

    <!-- Sort dropdown -->
    <select
      :value="props.sortBy"
      class="py-2 pl-3 pr-8 text-sm rounded-lg border border-ibook-brown-200 bg-white text-ibook-brown-700 focus:outline-none focus:ring-2 focus:ring-ibook-brown-400"
      @change="onSortChange"
    >
      <option value="distance">Nearest first</option>
      <option value="name">Name A-Z</option>
    </select>

    <!-- Price range -->
    <div class="flex items-center gap-1.5">
      <input
        type="number"
        :value="props.minPrice ?? ''"
        min="0"
        step="1000"
        placeholder="Min price"
        class="w-28 py-2 px-3 text-sm rounded-lg border border-ibook-brown-200 bg-white text-ibook-brown-700 placeholder-ibook-brown-400 focus:outline-none focus:ring-2 focus:ring-ibook-brown-400"
        @input="onMinPriceInput"
      />
      <span class="text-ibook-brown-400 text-sm font-medium">—</span>
      <input
        type="number"
        :value="props.maxPrice ?? ''"
        min="0"
        step="1000"
        placeholder="Max price"
        class="w-28 py-2 px-3 text-sm rounded-lg border border-ibook-brown-200 bg-white text-ibook-brown-700 placeholder-ibook-brown-400 focus:outline-none focus:ring-2 focus:ring-ibook-brown-400"
        @input="onMaxPriceInput"
      />
      <span class="text-xs text-ibook-brown-400">UZS</span>
    </div>
  </div>
</template>
