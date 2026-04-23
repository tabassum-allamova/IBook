<script setup lang="ts">
import { ref, computed, watch, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import { useDebounceFn } from '@vueuse/core'
import OwnerLayout from '@/layouts/OwnerLayout.vue'
import api from '@/lib/axios'

const toast = useToast()
const { t } = useI18n()
const router = useRouter()
const queryClient = useQueryClient()

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
  members: Member[]
}

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

// ---- Add barber modal ----
interface DirectoryBarber {
  id: number
  full_name: string
  email: string
  avatar: string | null
  shop_name: string | null
}

const isAddOpen = ref(false)
const searchInput = ref('')
const debouncedQuery = ref('')

const commitSearch = useDebounceFn((v: string) => {
  debouncedQuery.value = v.trim()
}, 300)

watch(searchInput, (v) => commitSearch(v))

const { data: searchResults, isFetching: isSearching } = useQuery<DirectoryBarber[]>({
  queryKey: computed(() => ['barber-directory', debouncedQuery.value, shop.value?.id]),
  queryFn: async () => {
    if (!shop.value) return []
    const res = await api.get<DirectoryBarber[]>('/api/barbers/', {
      params: { email: debouncedQuery.value, exclude_shop: shop.value.id },
    })
    return res.data.slice(0, 25)
  },
  // Only run the search once the owner has typed at least 2 characters.
  enabled: computed(
    () => isAddOpen.value && !!shop.value && debouncedQuery.value.length >= 2,
  ),
})

const addingId = ref<number | null>(null)

const addBarber = useMutation({
  mutationFn: (barberId: number) =>
    api.post(`/api/shops/${shop.value!.id}/members/`, { barber_id: barberId }),
  onMutate: (id: number) => {
    addingId.value = id
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['shop', 'owner'] })
    queryClient.invalidateQueries({ queryKey: ['barber-directory'] })
    toast.success('Barber added to shop')
    // One at a time: close + reset modal so the owner actively reopens for the next add.
    isAddOpen.value = false
    searchInput.value = ''
    debouncedQuery.value = ''
  },
  onError: (err: unknown) => {
    const e = err as { response?: { data?: { detail?: string } } }
    toast.error(e?.response?.data?.detail ?? 'Failed to add barber.')
  },
  onSettled: () => {
    addingId.value = null
  },
})

function openAdd() {
  searchInput.value = ''
  debouncedQuery.value = ''
  isAddOpen.value = true
}

function closeAdd() {
  if (addBarber.isPending.value) return
  isAddOpen.value = false
}

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && isAddOpen.value) closeAdd()
}

watch(isAddOpen, (open) => {
  if (typeof document === 'undefined') return
  document.body.style.overflow = open ? 'hidden' : ''
  if (open) window.addEventListener('keydown', onKeydown)
  else window.removeEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (typeof document !== 'undefined') document.body.style.overflow = ''
})

// ---- Remove barber ----
const removingId = ref<number | null>(null)
const pendingRemove = ref<Member | null>(null)

const removeBarber = useMutation({
  mutationFn: (barberId: number) =>
    api.delete(`/api/shops/${shop.value!.id}/members/${barberId}/`),
  onMutate: (id: number) => {
    removingId.value = id
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['shop', 'owner'] })
    queryClient.invalidateQueries({ queryKey: ['barber-directory'] })
    toast.success('Barber removed from shop')
    pendingRemove.value = null
  },
  onError: () => {
    toast.error('Failed to remove barber.')
  },
  onSettled: () => {
    removingId.value = null
  },
})

function confirmRemove() {
  if (!pendingRemove.value) return
  removeBarber.mutate(pendingRemove.value.barber.id)
}

function getInitials(name: string): string {
  return name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2)
}

function formatPrice(price: number): string {
  return price.toLocaleString('en-US') + ' UZS'
}
</script>

<template>
  <OwnerLayout>
    <section class="max-w-6xl mx-auto">
      <!-- Header -->
      <div class="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6 md:mb-8">
        <div>
          <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
            {{ t('owner.barbers.title') }}
          </h1>
          <p class="mt-1 text-sm text-slate-600">
            {{ t('owner.barbers.subtitle') }}
          </p>
        </div>

        <button
          type="button"
          class="inline-flex items-center justify-center gap-1.5 h-10 px-4 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 self-start sm:self-auto"
          :disabled="!shop"
          @click="openAdd"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m-8-8h16" />
          </svg>
          {{ t('owner.barbers.addBarber') }}
        </button>
      </div>

      <!-- Loading -->
      <div v-if="shopLoading" class="space-y-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <div v-for="i in 6" :key="i" class="h-40 bg-white border border-slate-200 rounded-xl p-4">
            <div class="h-12 w-12 rounded-full bg-slate-100 animate-pulse mb-3" />
            <div class="h-4 bg-slate-100 animate-pulse rounded w-2/3 mb-2" />
            <div class="h-3 bg-slate-100 animate-pulse rounded w-1/3" />
          </div>
        </div>
      </div>

      <!-- Content -->
      <template v-else-if="shop">
        <div class="flex items-baseline justify-between mb-4">
          <h2 class="text-base font-semibold text-slate-900 tracking-tight">Team</h2>
          <p class="text-sm text-slate-500">
            {{ shop.members.length }}
            {{ shop.members.length === 1 ? 'barber' : 'barbers' }}
          </p>
        </div>

        <!-- Grid -->
        <div
          v-if="shop.members.length > 0"
          class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 md:gap-5"
        >
          <div
            v-for="member in shop.members"
            :key="member.id"
            class="bg-white rounded-xl border border-slate-200 p-4 flex flex-col gap-3 hover:border-slate-300 transition-colors"
          >
            <div class="flex items-center gap-3">
              <div class="flex-shrink-0 w-12 h-12 rounded-full overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center">
                <img
                  v-if="member.barber.avatar"
                  :src="member.barber.avatar"
                  :alt="member.barber.full_name"
                  class="w-full h-full object-cover"
                />
                <span v-else class="text-sm font-semibold text-slate-500">
                  {{ getInitials(member.barber.full_name) }}
                </span>
              </div>
              <div class="min-w-0">
                <p class="text-sm font-semibold text-slate-900 truncate">
                  {{ member.barber.full_name }}
                </p>
                <p class="text-sm text-slate-500 truncate">{{ member.barber.email }}</p>
              </div>
            </div>

            <div v-if="member.barber.top_services.length > 0" class="space-y-1">
              <p
                v-for="svc in member.barber.top_services.slice(0, 3)"
                :key="svc.id"
                class="flex items-center justify-between text-sm text-slate-600"
              >
                <span class="truncate pr-2">{{ svc.name }}</span>
                <span class="font-medium text-slate-900 tabular-nums">{{ formatPrice(svc.price) }}</span>
              </p>
            </div>
            <p v-else class="text-sm text-slate-400">No services listed</p>

            <div class="mt-auto pt-2">
              <button
                type="button"
                class="text-sm font-medium text-red-600 hover:text-red-700 transition-colors disabled:opacity-50"
                :disabled="removingId === member.barber.id"
                @click="pendingRemove = member"
              >
                <span v-if="removingId === member.barber.id">Removing…</span>
                <span v-else>{{ t('owner.barbers.remove') }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Empty -->
        <div
          v-else
          class="py-16 text-center rounded-xl border border-dashed border-slate-200 bg-white"
        >
          <div class="inline-flex items-center justify-center w-12 h-12 rounded-lg bg-slate-100 mb-3">
            <svg class="h-6 w-6 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <p class="text-base font-semibold text-slate-900">No barbers yet</p>
          <p class="mt-1 text-sm text-slate-500 max-w-xs mx-auto">
            Click “Add barber” to invite someone to your team.
          </p>
        </div>
      </template>

      <!-- Add barber modal -->
      <Teleport to="body">
        <Transition name="fade">
          <div
            v-if="isAddOpen"
            class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-end md:items-center justify-center md:p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby="add-barber-title"
            @click.self="closeAdd"
          >
            <Transition name="slide-up">
              <div
                v-if="isAddOpen"
                class="w-full md:max-w-lg bg-white rounded-t-2xl md:rounded-2xl shadow-xl flex flex-col max-h-[85vh]"
              >
                <!-- Header -->
                <div class="flex items-start justify-between gap-4 px-5 md:px-6 py-4 border-b border-slate-200">
                  <div class="min-w-0">
                    <h2 id="add-barber-title" class="text-lg font-semibold text-slate-900 tracking-tight">
                      Add a barber
                    </h2>
                    <p class="mt-0.5 text-sm text-slate-500">
                      Search for a registered barber by their email.
                    </p>
                  </div>
                  <button
                    type="button"
                    aria-label="Close"
                    class="flex-shrink-0 h-9 w-9 inline-flex items-center justify-center rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors disabled:opacity-50"
                    :disabled="addBarber.isPending.value"
                    @click="closeAdd"
                  >
                    <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                <!-- Search -->
                <div class="px-5 md:px-6 pt-4 pb-3">
                  <label class="relative block">
                    <span class="sr-only">Search barbers</span>
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
                      v-model="searchInput"
                      type="email"
                      placeholder="barber@example.com"
                      autocomplete="off"
                      autofocus
                      class="w-full h-10 pl-10 pr-9 text-sm bg-white border border-slate-200 rounded-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:border-slate-900 focus:ring-4 focus:ring-slate-900/5 transition-colors"
                    />
                    <button
                      v-if="searchInput"
                      type="button"
                      aria-label="Clear search"
                      class="absolute right-2 top-1/2 -translate-y-1/2 h-6 w-6 inline-flex items-center justify-center rounded-md text-slate-400 hover:text-slate-900 hover:bg-slate-100 transition-colors"
                      @click="searchInput = ''"
                    >
                      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </label>
                </div>

                <!-- Results -->
                <div class="flex-1 overflow-y-auto px-2 md:px-3 pb-3">
                  <!-- Prompt: no search yet -->
                  <div
                    v-if="debouncedQuery.length < 2"
                    class="py-10 px-5 text-center"
                  >
                    <div class="inline-flex items-center justify-center w-10 h-10 rounded-lg bg-slate-100 mb-3">
                      <svg class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" stroke-width="1.6" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                      </svg>
                    </div>
                    <p class="text-sm font-semibold text-slate-900">Search by email</p>
                    <p class="mt-1 text-sm text-slate-500 max-w-xs mx-auto">
                      Type at least 2 characters of the barber's email to see matches.
                    </p>
                  </div>

                  <ul v-else-if="isSearching" class="space-y-0.5" aria-busy="true">
                    <li v-for="i in 4" :key="i">
                      <div class="flex items-center gap-3 px-3 md:px-4 py-3">
                        <div class="flex-shrink-0 w-10 h-10 rounded-full bg-slate-100 animate-pulse" />
                        <div class="flex-1 min-w-0 space-y-1.5">
                          <div class="h-4 bg-slate-100 animate-pulse rounded w-1/2" />
                          <div class="h-3 bg-slate-100 animate-pulse rounded w-2/3" />
                        </div>
                        <div class="h-9 w-16 bg-slate-100 animate-pulse rounded-lg" />
                      </div>
                    </li>
                  </ul>
                  <div
                    v-else-if="searchResults && searchResults.length === 0"
                    class="py-10 px-5 text-center"
                  >
                    <p class="text-sm font-semibold text-slate-900">No barbers found</p>
                    <p class="mt-1 text-sm text-slate-500">
                      No registered barber matches that email.
                    </p>
                  </div>
                  <ul v-else-if="searchResults" class="space-y-0.5">
                    <li v-for="b in searchResults" :key="b.id">
                      <div class="flex items-center gap-3 px-3 md:px-4 py-3 rounded-lg hover:bg-slate-50 transition-colors">
                        <div class="flex-shrink-0 w-10 h-10 rounded-full overflow-hidden bg-slate-100 border border-slate-200 flex items-center justify-center">
                          <img
                            v-if="b.avatar"
                            :src="b.avatar"
                            :alt="b.full_name"
                            class="w-full h-full object-cover"
                          />
                          <span v-else class="text-sm font-semibold text-slate-500">
                            {{ getInitials(b.full_name) }}
                          </span>
                        </div>
                        <div class="flex-1 min-w-0">
                          <p class="text-sm font-semibold text-slate-900 truncate">{{ b.full_name }}</p>
                          <p class="text-sm text-slate-500 truncate">{{ b.email }}</p>
                          <p v-if="b.shop_name" class="text-sm text-slate-400 truncate">
                            Currently at {{ b.shop_name }}
                          </p>
                        </div>
                        <button
                          type="button"
                          class="flex-shrink-0 inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                          :disabled="addingId === b.id || addBarber.isPending.value"
                          @click="addBarber.mutate(b.id)"
                        >
                          <svg
                            v-if="addingId === b.id"
                            class="h-4 w-4 animate-spin"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                            <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                          </svg>
                          {{ addingId === b.id ? 'Adding…' : 'Add' }}
                        </button>
                      </div>
                    </li>
                  </ul>
                </div>
              </div>
            </Transition>
          </div>
        </Transition>
      </Teleport>

      <!-- Remove confirm modal -->
      <Teleport to="body">
        <div
          v-if="pendingRemove"
          class="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-sm flex items-end md:items-center justify-center md:p-4"
          role="dialog"
          aria-modal="true"
          @click.self="pendingRemove = null"
        >
          <div class="w-full md:max-w-md bg-white rounded-t-2xl md:rounded-2xl shadow-xl p-5 md:p-6">
            <h3 class="text-lg font-semibold text-slate-900 tracking-tight">
              Remove this barber?
            </h3>
            <p class="mt-2 text-sm text-slate-600">
              {{ pendingRemove.barber.full_name }} will no longer appear on your shop page or in customer searches.
            </p>
            <div class="mt-6 flex flex-col-reverse sm:flex-row sm:justify-end gap-2">
              <button
                type="button"
                class="inline-flex items-center justify-center h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors disabled:opacity-50"
                :disabled="removeBarber.isPending.value"
                @click="pendingRemove = null"
              >
                Keep barber
              </button>
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 h-10 px-4 rounded-lg bg-red-600 hover:bg-red-700 text-white text-sm font-semibold transition-colors disabled:opacity-60"
                :disabled="removeBarber.isPending.value"
                @click="confirmRemove"
              >
                <svg
                  v-if="removeBarber.isPending.value"
                  class="h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                  <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                </svg>
                Remove
              </button>
            </div>
          </div>
        </div>
      </Teleport>
    </section>
  </OwnerLayout>
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
