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

const ratingOptions: Array<{ label: string; value: number }> = [
  { label: 'All', value: 0 },
  { label: '3+', value: 3 },
  { label: '4+', value: 4 },
  { label: '5', value: 5 },
]

function onSearchInput(e: Event) {
  emit('update:search', (e.target as HTMLInputElement).value)
}

function clearSearch() {
  emit('update:search', '')
}

function setRating(value: number) {
  emit('update:minRating', value)
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
  <div class="space-y-4">
    <!-- Search -->
    <label class="relative block">
      <span class="sr-only">Search barbershops</span>
      <svg
        class="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400 pointer-events-none"
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
        :value="props.search"
        placeholder="Search barbershops by name"
        class="w-full pl-11 pr-10 py-3 text-[15px] bg-white border border-slate-200 rounded-xl text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition"
        @input="onSearchInput"
      />
      <button
        v-if="props.search"
        type="button"
        aria-label="Clear search"
        class="absolute right-3 top-1/2 -translate-y-1/2 h-7 w-7 inline-flex items-center justify-center rounded-md text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors"
        @click="clearSearch"
      >
        <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </label>

    <!-- Filter row -->
    <div class="flex flex-col lg:flex-row lg:items-center gap-3 lg:gap-4">
      <!-- Rating segmented control -->
      <div class="flex items-center gap-3">
        <span class="text-sm font-medium text-slate-600 flex-shrink-0">Rating</span>
        <div class="inline-flex items-center rounded-lg border border-slate-200 bg-white p-0.5">
          <button
            v-for="opt in ratingOptions"
            :key="opt.value"
            type="button"
            :class="[
              'px-3 py-1.5 text-[13px] font-medium rounded-md transition-colors',
              props.minRating === opt.value
                ? 'bg-slate-900 text-white'
                : 'text-slate-600 hover:text-slate-900',
            ]"
            @click="setRating(opt.value)"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>

      <!-- Price -->
      <div class="flex items-center gap-3">
        <span class="text-sm font-medium text-slate-600 flex-shrink-0">Price</span>
        <div class="inline-flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-1.5 focus-within:border-slate-900 focus-within:ring-4 focus-within:ring-slate-900/5 transition">
          <input
            type="number"
            :value="props.minPrice ?? ''"
            min="0"
            step="10000"
            placeholder="Min"
            inputmode="numeric"
            class="w-16 bg-transparent text-[13px] tabular-nums text-slate-900 placeholder:text-slate-400 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            @input="onMinPriceInput"
          />
          <span class="text-slate-300 text-sm">–</span>
          <input
            type="number"
            :value="props.maxPrice ?? ''"
            min="0"
            step="10000"
            placeholder="Max"
            inputmode="numeric"
            class="w-16 bg-transparent text-[13px] tabular-nums text-slate-900 placeholder:text-slate-400 focus:outline-none [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            @input="onMaxPriceInput"
          />
          <span class="text-[11px] font-medium text-slate-400 uppercase tracking-wide pl-1 border-l border-slate-200 ml-0.5">UZS</span>
        </div>
      </div>

      <!-- Sort -->
      <div class="flex items-center gap-3 lg:ml-auto">
        <span class="text-sm font-medium text-slate-600 flex-shrink-0">Sort by</span>
        <div class="relative">
          <select
            :value="props.sortBy"
            class="appearance-none bg-white border border-slate-200 rounded-lg pl-3 pr-9 py-2 text-[13px] font-medium text-slate-900 cursor-pointer focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition"
            @change="onSortChange"
          >
            <option value="distance">Nearest first</option>
            <option value="name">Name A–Z</option>
          </select>
          <svg
            class="absolute right-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-slate-500 pointer-events-none"
            viewBox="0 0 12 8"
            fill="none"
            stroke="currentColor"
            stroke-width="1.8"
          >
            <path d="M1 1.5 L6 6.5 L11 1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>
