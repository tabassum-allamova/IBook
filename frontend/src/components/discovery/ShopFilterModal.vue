<script setup lang="ts">
import { onMounted, onUnmounted, watch } from 'vue'

const props = defineProps<{
  open: boolean
  minRating: number
  sortBy: string
  minPrice: number | null
  maxPrice: number | null
  resultCount: number
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update:minRating', value: number): void
  (e: 'update:sortBy', value: string): void
  (e: 'update:minPrice', value: number | null): void
  (e: 'update:maxPrice', value: number | null): void
  (e: 'clear'): void
}>()

const ratingOptions: Array<{ label: string; value: number }> = [
  { label: 'Any', value: 0 },
  { label: '3+', value: 3 },
  { label: '4+', value: 4 },
  { label: '5 only', value: 5 },
]

const sortOptions: Array<{ label: string; description: string; value: string }> = [
  { label: 'Nearest first', description: 'Closest to your location', value: 'distance' },
  { label: 'Name A–Z', description: 'Alphabetical order', value: 'name' },
]

function setRating(value: number) {
  emit('update:minRating', value)
}

function onMinPriceInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  emit('update:minPrice', val === '' ? null : Number(val))
}

function onMaxPriceInput(e: Event) {
  const val = (e.target as HTMLInputElement).value
  emit('update:maxPrice', val === '' ? null : Number(val))
}

function setSort(value: string) {
  emit('update:sortBy', value)
}

function close() {
  emit('close')
}

function clearAll() {
  emit('clear')
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && props.open) close()
}

onMounted(() => {
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})

// Lock body scroll while open
watch(
  () => props.open,
  (isOpen) => {
    if (typeof document === 'undefined') return
    document.body.style.overflow = isOpen ? 'hidden' : ''
  },
)
</script>

<template>
  <Teleport to="body">
    <Transition name="fade">
      <div
        v-if="props.open"
        class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-end md:items-center justify-center md:p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="filter-modal-title"
        @click.self="close"
      >
        <Transition name="slide-up">
          <div
            v-if="props.open"
            class="w-full md:max-w-md bg-white rounded-t-2xl md:rounded-2xl shadow-xl flex flex-col max-h-[85vh]"
          >
            <!-- Header -->
            <div class="flex items-center justify-between px-5 md:px-6 py-4 border-b border-slate-200">
              <h2 id="filter-modal-title" class="text-lg font-semibold text-slate-900 tracking-tight">
                Filters
              </h2>
              <button
                type="button"
                aria-label="Close filters"
                class="h-9 w-9 inline-flex items-center justify-center rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                @click="close"
              >
                <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <!-- Body -->
            <div class="flex-1 overflow-y-auto px-5 md:px-6 py-5 space-y-7">
              <!-- Minimum rating -->
              <div>
                <h3 class="text-sm font-semibold text-slate-900 mb-3">Minimum rating</h3>
                <div class="grid grid-cols-4 gap-2">
                  <button
                    v-for="opt in ratingOptions"
                    :key="opt.value"
                    type="button"
                    :class="[
                      'px-3 py-2.5 text-sm font-medium rounded-lg border transition-colors text-center',
                      props.minRating === opt.value
                        ? 'bg-slate-900 text-white border-slate-900'
                        : 'bg-white text-slate-700 border-slate-200 hover:border-slate-400',
                    ]"
                    @click="setRating(opt.value)"
                  >
                    {{ opt.label }}
                  </button>
                </div>
              </div>

              <!-- Price range -->
              <div>
                <h3 class="text-sm font-semibold text-slate-900 mb-3">Price range</h3>
                <div class="flex items-center gap-3">
                  <label class="flex-1">
                    <span class="block text-xs font-medium text-slate-500 mb-1">Min</span>
                    <div class="relative">
                      <input
                        type="number"
                        :value="props.minPrice ?? ''"
                        min="0"
                        step="10000"
                        placeholder="0"
                        inputmode="numeric"
                        class="w-full bg-white border border-slate-200 rounded-lg pl-3 pr-12 py-2.5 text-sm tabular-nums text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        @input="onMinPriceInput"
                      />
                      <span class="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] font-medium uppercase tracking-wide text-slate-400 pointer-events-none">
                        UZS
                      </span>
                    </div>
                  </label>
                  <span class="text-slate-300 mt-5">—</span>
                  <label class="flex-1">
                    <span class="block text-xs font-medium text-slate-500 mb-1">Max</span>
                    <div class="relative">
                      <input
                        type="number"
                        :value="props.maxPrice ?? ''"
                        min="0"
                        step="10000"
                        placeholder="Any"
                        inputmode="numeric"
                        class="w-full bg-white border border-slate-200 rounded-lg pl-3 pr-12 py-2.5 text-sm tabular-nums text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
                        @input="onMaxPriceInput"
                      />
                      <span class="absolute right-3 top-1/2 -translate-y-1/2 text-[11px] font-medium uppercase tracking-wide text-slate-400 pointer-events-none">
                        UZS
                      </span>
                    </div>
                  </label>
                </div>
              </div>

              <!-- Sort by -->
              <div>
                <h3 class="text-sm font-semibold text-slate-900 mb-3">Sort by</h3>
                <div class="space-y-2">
                  <button
                    v-for="opt in sortOptions"
                    :key="opt.value"
                    type="button"
                    :class="[
                      'w-full flex items-center justify-between gap-3 px-4 py-3 rounded-lg border text-left transition-colors',
                      props.sortBy === opt.value
                        ? 'border-slate-900 bg-slate-50'
                        : 'border-slate-200 hover:border-slate-400',
                    ]"
                    @click="setSort(opt.value)"
                  >
                    <span class="min-w-0">
                      <span class="block text-sm font-medium text-slate-900">{{ opt.label }}</span>
                      <span class="block text-xs text-slate-500 mt-0.5">{{ opt.description }}</span>
                    </span>
                    <span
                      :class="[
                        'h-4 w-4 rounded-full border-2 flex-shrink-0 transition-colors',
                        props.sortBy === opt.value
                          ? 'border-slate-900 bg-slate-900 ring-2 ring-inset ring-white'
                          : 'border-slate-300',
                      ]"
                    />
                  </button>
                </div>
              </div>
            </div>

            <!-- Footer -->
            <div class="flex items-center justify-between gap-3 px-5 md:px-6 py-4 border-t border-slate-200 bg-white rounded-b-2xl md:rounded-b-2xl">
              <button
                type="button"
                class="text-sm font-medium text-slate-600 hover:text-slate-900 underline underline-offset-4 decoration-slate-300 hover:decoration-slate-900 transition-colors"
                @click="clearAll"
              >
                Clear all
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center px-5 py-2.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
                @click="close"
              >
                Show {{ props.resultCount }}
                {{ props.resultCount === 1 ? 'result' : 'results' }}
              </button>
            </div>
          </div>
        </Transition>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.18s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.22s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.18s ease;
}
.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(16px);
  opacity: 0;
}
@media (min-width: 768px) {
  .slide-up-enter-from,
  .slide-up-leave-to {
    transform: scale(0.97);
  }
}
</style>
