<script setup lang="ts">
import { reactive, ref, computed, watch, markRaw, shallowRef } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'

const { t } = useI18n()
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import markerIcon2x from 'leaflet/dist/images/marker-icon-2x.png'
import markerIcon from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'
import { LMap, LTileLayer, LMarker } from '@vue-leaflet/vue-leaflet'
import OwnerLayout from '@/layouts/OwnerLayout.vue'
import api from '@/lib/axios'

// Vite icon fix (idempotent)
;(globalThis as unknown as Record<string, unknown>).L = L
delete (L.Icon.Default.prototype as unknown as Record<string, unknown>)._getIconUrl
L.Icon.Default.mergeOptions({
  iconUrl: markerIcon,
  iconRetinaUrl: markerIcon2x,
  shadowUrl: markerShadow,
})

const toast = useToast()
const router = useRouter()
const queryClient = useQueryClient()

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

interface Shop {
  id: number
  name: string
  address: string
  lat: string | null
  lng: string | null
  description: string
  hours: ShopHours[]
  photos: ShopPhoto[]
  members: { id: number }[]
  created_at: string
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

const DAY_NAMES = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

// ── Details form ──────────────────────────────────────────────────────────────
const TASHKENT_CENTER: [number, number] = [41.2995, 69.2401]

const details = reactive({
  name: '',
  address: '',
  description: '',
  lat: null as number | null,
  lng: null as number | null,
})
const detailsErrors = reactive({ name: '', address: '', description: '', location: '', general: '' })

function resetDetailsErrors() {
  detailsErrors.name = ''
  detailsErrors.address = ''
  detailsErrors.description = ''
  detailsErrors.location = ''
  detailsErrors.general = ''
}

// Leaflet must see plain tuples (not Vue proxies).
const mapCenter = shallowRef<[number, number]>(markRaw(TASHKENT_CENTER))
const markerPos = shallowRef<[number, number] | null>(null)

function applyLocation(lat: number, lng: number) {
  details.lat = Number(lat.toFixed(6))
  details.lng = Number(lng.toFixed(6))
  markerPos.value = markRaw<[number, number]>([details.lat, details.lng])
  mapCenter.value = markerPos.value
}

watch(
  shop,
  (s) => {
    if (s) {
      details.name = s.name ?? ''
      details.address = s.address ?? ''
      details.description = s.description ?? ''
      const lat = s.lat !== null ? Number(s.lat) : null
      const lng = s.lng !== null ? Number(s.lng) : null
      details.lat = lat
      details.lng = lng
      if (lat !== null && lng !== null) {
        markerPos.value = markRaw<[number, number]>([lat, lng])
        mapCenter.value = markerPos.value
      } else {
        markerPos.value = null
        mapCenter.value = markRaw(TASHKENT_CENTER)
      }
    }
  },
  { immediate: true },
)

const detailsDirty = computed(() => {
  if (!shop.value) return false
  const origLat = shop.value.lat !== null ? Number(shop.value.lat) : null
  const origLng = shop.value.lng !== null ? Number(shop.value.lng) : null
  return (
    details.name !== (shop.value.name ?? '') ||
    details.address !== (shop.value.address ?? '') ||
    details.description !== (shop.value.description ?? '') ||
    details.lat !== origLat ||
    details.lng !== origLng
  )
})

// Reverse geocode via Nominatim (OpenStreetMap).
// Rate-limited to 1 req/s by their policy; we only fire on explicit user interactions.
const isReverseGeocoding = ref(false)

async function reverseGeocode(lat: number, lng: number) {
  isReverseGeocoding.value = true
  try {
    const url = new URL('https://nominatim.openstreetmap.org/reverse')
    url.searchParams.set('format', 'jsonv2')
    url.searchParams.set('lat', String(lat))
    url.searchParams.set('lon', String(lng))
    url.searchParams.set('addressdetails', '1')
    url.searchParams.set('accept-language', 'en')
    url.searchParams.set('zoom', '18')
    const res = await fetch(url.toString(), {
      headers: { 'Accept': 'application/json' },
    })
    if (!res.ok) throw new Error(`${res.status}`)
    const data = (await res.json()) as {
      display_name?: string
      address?: Record<string, string | undefined>
    }
    const a = data.address ?? {}
    // Prefer "street + locality" style output; fall back to Nominatim's display_name.
    const streetParts = [
      [a.house_number, a.road].filter(Boolean).join(' '),
      a.neighbourhood || a.suburb,
      a.city || a.town || a.village || a.county,
    ]
      .filter(Boolean)
      .join(', ')
    details.address = streetParts || data.display_name || details.address
  } catch {
    toast.error('Couldn\'t fetch address from the map. You can type it manually.')
  } finally {
    isReverseGeocoding.value = false
  }
}

function onMapClick(e: { latlng: { lat: number; lng: number } }) {
  applyLocation(e.latlng.lat, e.latlng.lng)
  reverseGeocode(e.latlng.lat, e.latlng.lng)
}

function onMarkerDragEnd(e: { target: L.Marker }) {
  const latlng = e.target.getLatLng()
  applyLocation(latlng.lat, latlng.lng)
  reverseGeocode(latlng.lat, latlng.lng)
}

function validateDetails(): boolean {
  resetDetailsErrors()
  let ok = true
  if (!details.name.trim()) {
    detailsErrors.name = 'Shop name is required.'
    ok = false
  } else if (details.name.length > 100) {
    detailsErrors.name = 'Name is too long (max 100 characters).'
    ok = false
  }
  if (!details.address.trim()) {
    detailsErrors.address = 'Address is required.'
    ok = false
  } else if (details.address.length > 200) {
    detailsErrors.address = 'Address is too long (max 200 characters).'
    ok = false
  }
  if (details.description.length > 1000) {
    detailsErrors.description = 'Description is too long (max 1000 characters).'
    ok = false
  }
  if (details.lat === null || details.lng === null) {
    detailsErrors.location = 'Pick your shop location on the map.'
    ok = false
  }
  return ok
}

const saveDetails = useMutation({
  mutationFn: () =>
    api
      .patch(`/api/shops/${shop.value!.id}/`, {
        name: details.name.trim(),
        address: details.address.trim(),
        description: details.description,
        lat: details.lat,
        lng: details.lng,
      })
      .then((r) => r.data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['shop', 'owner'] })
    toast.success('Shop details updated')
    resetDetailsErrors()
  },
  onError: (err: unknown) => {
    const data = (err as { response?: { data?: Record<string, unknown> } }).response?.data
    const first = (v: unknown) =>
      typeof v === 'string' ? v : Array.isArray(v) && typeof v[0] === 'string' ? v[0] : ''
    if (data) {
      detailsErrors.name = first(data.name) || detailsErrors.name
      detailsErrors.address = first(data.address) || detailsErrors.address
      detailsErrors.description = first(data.description) || detailsErrors.description
      const latErr = first(data.lat)
      const lngErr = first(data.lng)
      if (latErr || lngErr) detailsErrors.location = latErr || lngErr
      if (
        !detailsErrors.name &&
        !detailsErrors.address &&
        !detailsErrors.description &&
        !detailsErrors.location
      ) {
        detailsErrors.general = first(data.detail) || 'Failed to update shop.'
      }
    } else {
      detailsErrors.general = 'Failed to update shop.'
    }
    toast.error('Failed to update shop.')
  },
})

function onSaveDetails() {
  if (!validateDetails()) return
  saveDetails.mutate()
}

// ── Hours form ────────────────────────────────────────────────────────────────
interface HourRow {
  day_of_week: number
  is_open: boolean
  opens_at: string
  closes_at: string
  has_break: boolean
  break_start: string
  break_end: string
}

const hoursRows = ref<HourRow[]>([])
const hoursError = ref('')

function rowFromShop(h: ShopHours): HourRow {
  return {
    day_of_week: h.day_of_week,
    is_open: h.is_open,
    opens_at: (h.opens_at ?? '').slice(0, 5) || '09:00',
    closes_at: (h.closes_at ?? '').slice(0, 5) || '18:00',
    has_break: Boolean(h.break_start && h.break_end),
    break_start: (h.break_start ?? '').slice(0, 5) || '13:00',
    break_end: (h.break_end ?? '').slice(0, 5) || '14:00',
  }
}

function seedDefaultRows(): HourRow[] {
  return Array.from({ length: 7 }, (_, i) => ({
    day_of_week: i,
    is_open: i < 6,
    opens_at: '09:00',
    closes_at: '18:00',
    has_break: false,
    break_start: '13:00',
    break_end: '14:00',
  }))
}

watch(
  shop,
  (s) => {
    if (!s) return
    if (s.hours && s.hours.length > 0) {
      const byDay = new Map(s.hours.map((h) => [h.day_of_week, h]))
      hoursRows.value = Array.from({ length: 7 }, (_, i) =>
        byDay.has(i) ? rowFromShop(byDay.get(i) as ShopHours) : rowFromShop({
          id: 0,
          day_of_week: i,
          is_open: false,
          opens_at: null,
          closes_at: null,
          break_start: null,
          break_end: null,
        }),
      )
    } else {
      hoursRows.value = seedDefaultRows()
    }
  },
  { immediate: true },
)

function validateHours(): boolean {
  hoursError.value = ''
  for (const r of hoursRows.value) {
    if (!r.is_open) continue
    if (!r.opens_at || !r.closes_at) {
      hoursError.value = `${DAY_NAMES[r.day_of_week]}: set both opening and closing times.`
      return false
    }
    if (r.opens_at >= r.closes_at) {
      hoursError.value = `${DAY_NAMES[r.day_of_week]}: closing time must be after opening time.`
      return false
    }
    if (r.has_break) {
      if (!r.break_start || !r.break_end) {
        hoursError.value = `${DAY_NAMES[r.day_of_week]}: set both break start and end.`
        return false
      }
      if (r.break_start >= r.break_end) {
        hoursError.value = `${DAY_NAMES[r.day_of_week]}: break end must be after break start.`
        return false
      }
      if (r.break_start < r.opens_at || r.break_end > r.closes_at) {
        hoursError.value = `${DAY_NAMES[r.day_of_week]}: break must fall within opening hours.`
        return false
      }
    }
  }
  return true
}

const saveHours = useMutation({
  mutationFn: () => {
    const payload = hoursRows.value.map((r) => ({
      day_of_week: r.day_of_week,
      is_open: r.is_open,
      opens_at: r.is_open ? `${r.opens_at}:00` : null,
      closes_at: r.is_open ? `${r.closes_at}:00` : null,
      break_start: r.is_open && r.has_break ? `${r.break_start}:00` : null,
      break_end: r.is_open && r.has_break ? `${r.break_end}:00` : null,
    }))
    return api
      .put(`/api/shops/${shop.value!.id}/hours/`, payload)
      .then((r) => r.data)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['shop', 'owner'] })
    toast.success('Opening hours updated')
    hoursError.value = ''
  },
  onError: () => {
    toast.error('Failed to update hours.')
  },
})

function onSaveHours() {
  if (!validateHours()) return
  saveHours.mutate()
}

// ── Photos ────────────────────────────────────────────────────────────────────
const photoFileInput = ref<HTMLInputElement | null>(null)

function openPhotoPicker() {
  photoFileInput.value?.click()
}

const uploadPhotos = useMutation({
  mutationFn: (files: File[]) => {
    const fd = new FormData()
    for (const f of files) fd.append('image', f)
    return api.post(`/api/shops/${shop.value!.id}/photos/`, fd).then((r) => r.data)
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['shop', 'owner'] })
    toast.success('Photos uploaded')
    if (photoFileInput.value) photoFileInput.value.value = ''
  },
  onError: (err: unknown) => {
    const msg =
      (err as { response?: { data?: { error?: string } } })?.response?.data?.error ??
      'Failed to upload photos.'
    toast.error(msg)
    if (photoFileInput.value) photoFileInput.value.value = ''
  },
})

function onPhotoChange(e: Event) {
  const target = e.target as HTMLInputElement
  const files = Array.from(target.files ?? [])
  if (files.length === 0) return
  for (const f of files) {
    if (!f.type.startsWith('image/')) {
      toast.error(`${f.name} is not an image.`)
      return
    }
    if (f.size > 5 * 1024 * 1024) {
      toast.error(`${f.name} is larger than 5 MB.`)
      return
    }
  }
  const remaining = 5 - (shop.value?.photos.length ?? 0)
  if (files.length > remaining) {
    toast.error(`You can only upload ${remaining} more ${remaining === 1 ? 'photo' : 'photos'} (max 5).`)
    if (photoFileInput.value) photoFileInput.value.value = ''
    return
  }
  uploadPhotos.mutate(files)
}

const deletingPhotoId = ref<number | null>(null)

const deletePhoto = useMutation({
  mutationFn: (photoId: number) =>
    api.delete(`/api/shops/${shop.value!.id}/photos/${photoId}/`).then((r) => r.data),
  onMutate: (id: number) => {
    deletingPhotoId.value = id
  },
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['shop', 'owner'] })
    toast.success('Photo removed')
  },
  onError: () => {
    toast.error('Failed to remove photo.')
  },
  onSettled: () => {
    deletingPhotoId.value = null
  },
})

function removePhoto(id: number) {
  deletePhoto.mutate(id)
}
</script>

<template>
  <OwnerLayout>
    <section class="max-w-6xl mx-auto">
      <!-- Loading -->
      <div v-if="shopLoading" class="space-y-5">
        <div class="h-8 w-64 bg-slate-100 animate-pulse rounded" />
        <div class="h-4 w-96 bg-slate-100 animate-pulse rounded" />
        <div v-for="i in 3" :key="i" class="bg-white rounded-xl border border-slate-200 p-6 h-48">
          <div class="h-4 w-1/3 bg-slate-100 animate-pulse rounded mb-4" />
          <div class="h-10 bg-slate-100 animate-pulse rounded" />
        </div>
      </div>

      <!-- Content -->
      <template v-else-if="shop">
        <!-- Header -->
        <div class="mb-6 md:mb-8">
          <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
            {{ t('owner.shop.title') }}
          </h1>
          <p class="mt-1 text-sm text-slate-600">
            {{ t('owner.shop.subtitle') }}
          </p>
        </div>

        <div class="space-y-5 md:space-y-6">
          <!-- Details card -->
          <div class="bg-white rounded-xl border border-slate-200 p-6 md:p-8">
            <div class="flex items-baseline justify-between mb-5">
              <div>
                <h2 class="text-base font-semibold text-slate-900 tracking-tight">Details</h2>
                <p class="mt-0.5 text-sm text-slate-500">Shop name, address, and a short description.</p>
              </div>
            </div>

            <form class="max-w-2xl space-y-5" @submit.prevent="onSaveDetails">
              <div>
                <label for="shop-name" class="block text-sm font-medium text-slate-700 mb-1.5">
                  Shop name
                </label>
                <input
                  id="shop-name"
                  v-model="details.name"
                  type="text"
                  class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors"
                  :class="detailsErrors.name ? 'border-red-400 focus:ring-red-200' : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'"
                />
                <p v-if="detailsErrors.name" class="mt-1.5 text-sm text-red-600">{{ detailsErrors.name }}</p>
              </div>

              <div>
                <div class="flex items-center justify-between mb-1.5">
                  <label for="shop-address" class="block text-sm font-medium text-slate-700">
                    Location
                  </label>
                  <span v-if="isReverseGeocoding" class="text-sm text-slate-400 inline-flex items-center gap-1.5">
                    <svg class="h-3 w-3 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                      <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                    </svg>
                    Looking up address…
                  </span>
                </div>

                <!-- Map -->
                <div class="relative isolate rounded-xl overflow-hidden border border-slate-200 bg-slate-100 h-64 mb-3">
                  <LMap
                    :zoom="14"
                    :center="mapCenter"
                    :use-global-leaflet="true"
                    :zoom-control="true"
                    :attribution-control="false"
                    style="height: 100%; width: 100%;"
                    @click="onMapClick"
                  >
                    <LTileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    <LMarker
                      v-if="markerPos"
                      :lat-lng="markerPos"
                      :draggable="true"
                      @moveend="onMarkerDragEnd"
                    />
                  </LMap>

                  <!-- Floating hint (only visible before a pin is placed) -->
                  <div
                    v-if="!markerPos"
                    class="pointer-events-none absolute top-3 left-1/2 -translate-x-1/2 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-slate-900/90 text-white text-sm font-medium shadow-lg backdrop-blur z-[1000]"
                  >
                    <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                      <path stroke-linecap="round" stroke-linejoin="round" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                    </svg>
                    Click the map to set your location
                  </div>
                </div>

                <input
                  id="shop-address"
                  :value="details.address"
                  type="text"
                  readonly
                  placeholder="Pick a location on the map"
                  class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-700 placeholder:text-slate-400 bg-slate-50 cursor-not-allowed"
                  :class="detailsErrors.address ? 'border-red-400' : 'border-slate-200'"
                />

                <p v-if="detailsErrors.address" class="mt-1.5 text-sm text-red-600">{{ detailsErrors.address }}</p>
                <p v-if="detailsErrors.location" class="mt-1.5 text-sm text-red-600">{{ detailsErrors.location }}</p>
              </div>

              <div>
                <label for="shop-description" class="block text-sm font-medium text-slate-700 mb-1.5">
                  Description
                  <span class="font-normal text-slate-400">(optional)</span>
                </label>
                <textarea
                  id="shop-description"
                  v-model="details.description"
                  rows="4"
                  placeholder="Tell customers what makes your shop special…"
                  class="w-full px-3.5 py-2.5 rounded-lg border text-[15px] text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 transition-colors resize-none"
                  :class="detailsErrors.description ? 'border-red-400 focus:ring-red-200' : 'border-slate-200 focus:ring-slate-900/20 focus:border-slate-900'"
                ></textarea>
                <p v-if="detailsErrors.description" class="mt-1.5 text-sm text-red-600">{{ detailsErrors.description }}</p>
              </div>

              <div
                v-if="detailsErrors.general"
                class="px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
              >
                {{ detailsErrors.general }}
              </div>

              <div class="pt-2">
                <button
                  type="submit"
                  class="inline-flex items-center justify-center gap-2 h-10 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  :disabled="!detailsDirty || saveDetails.isPending.value"
                >
                  <svg
                    v-if="saveDetails.isPending.value"
                    class="h-4 w-4 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                    <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                  </svg>
                  {{ saveDetails.isPending.value ? 'Saving…' : 'Save details' }}
                </button>
              </div>
            </form>
          </div>

          <!-- Hours card -->
          <div class="bg-white rounded-xl border border-slate-200 p-6 md:p-8">
            <div class="mb-5">
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">Opening hours</h2>
              <p class="mt-0.5 text-sm text-slate-500">Set your weekly schedule. Toggle a day off or add a break.</p>
            </div>

            <ul class="divide-y divide-slate-100">
              <li
                v-for="row in hoursRows"
                :key="row.day_of_week"
                class="py-4 flex flex-col sm:flex-row sm:items-start gap-3"
              >
                <div class="w-32 flex items-center gap-3">
                  <label class="inline-flex items-center gap-2 cursor-pointer select-none">
                    <input
                      type="checkbox"
                      v-model="row.is_open"
                      class="h-4 w-4 accent-slate-900"
                    />
                    <span class="text-sm font-medium text-slate-900">{{ DAY_NAMES[row.day_of_week] }}</span>
                  </label>
                </div>

                <div class="flex-1 space-y-2">
                  <div v-if="row.is_open" class="flex flex-wrap items-center gap-2 text-sm text-slate-700">
                    <input
                      v-model="row.opens_at"
                      type="time"
                      class="h-9 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
                    />
                    <span class="text-slate-400">–</span>
                    <input
                      v-model="row.closes_at"
                      type="time"
                      class="h-9 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
                    />
                    <label class="inline-flex items-center gap-2 ml-3 text-sm text-slate-700 cursor-pointer select-none">
                      <input
                        type="checkbox"
                        v-model="row.has_break"
                        class="h-4 w-4 accent-slate-900"
                      />
                      Break
                    </label>
                    <template v-if="row.has_break">
                      <input
                        v-model="row.break_start"
                        type="time"
                        class="h-9 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
                      />
                      <span class="text-slate-400">–</span>
                      <input
                        v-model="row.break_end"
                        type="time"
                        class="h-9 px-3 rounded-lg border border-slate-200 text-sm text-slate-900 bg-white focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 tabular-nums"
                      />
                    </template>
                  </div>
                  <p v-else class="text-sm text-slate-400">Closed</p>
                </div>
              </li>
            </ul>

            <div
              v-if="hoursError"
              class="mt-4 px-4 py-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700"
            >
              {{ hoursError }}
            </div>

            <div class="pt-5">
              <button
                type="button"
                class="inline-flex items-center justify-center gap-2 h-10 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                :disabled="saveHours.isPending.value"
                @click="onSaveHours"
              >
                <svg
                  v-if="saveHours.isPending.value"
                  class="h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                  <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                </svg>
                {{ saveHours.isPending.value ? 'Saving…' : 'Save hours' }}
              </button>
            </div>
          </div>

          <!-- Photos card -->
          <div class="bg-white rounded-xl border border-slate-200 p-6 md:p-8">
            <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3 mb-5">
              <div>
                <h2 class="text-base font-semibold text-slate-900 tracking-tight">Photos</h2>
                <p class="mt-0.5 text-sm text-slate-500">Up to 5 photos, JPG or PNG, 5 MB each.</p>
              </div>
              <button
                type="button"
                class="inline-flex items-center gap-1.5 h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors disabled:opacity-60 disabled:cursor-not-allowed self-start"
                :disabled="(shop.photos.length >= 5) || uploadPhotos.isPending.value"
                @click="openPhotoPicker"
              >
                <svg
                  v-if="uploadPhotos.isPending.value"
                  class="h-4 w-4 animate-spin"
                  fill="none"
                  viewBox="0 0 24 24"
                >
                  <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                  <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                </svg>
                <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M12 4v16m-8-8h16" />
                </svg>
                {{ uploadPhotos.isPending.value ? 'Uploading…' : 'Upload photos' }}
              </button>
              <input
                ref="photoFileInput"
                type="file"
                accept="image/png,image/jpeg,image/webp"
                multiple
                class="hidden"
                @change="onPhotoChange"
              />
            </div>

            <div
              v-if="shop.photos.length > 0"
              class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3"
            >
              <div
                v-for="photo in shop.photos"
                :key="photo.id"
                class="relative aspect-square rounded-lg overflow-hidden bg-slate-100 border border-slate-200 group"
              >
                <img
                  :src="photo.image"
                  :alt="shop.name + ' photo'"
                  class="w-full h-full object-cover"
                  loading="lazy"
                />
                <button
                  type="button"
                  class="absolute top-2 right-2 inline-flex items-center justify-center h-8 w-8 rounded-md bg-white/95 text-red-600 hover:text-red-700 border border-slate-200 shadow-sm opacity-0 group-hover:opacity-100 focus:opacity-100 transition-opacity disabled:opacity-60"
                  :disabled="deletingPhotoId === photo.id"
                  aria-label="Remove photo"
                  @click="removePhoto(photo.id)"
                >
                  <svg
                    v-if="deletingPhotoId === photo.id"
                    class="h-4 w-4 animate-spin"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
                    <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
                  </svg>
                  <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6M1 7h22M9 7V5a2 2 0 012-2h2a2 2 0 012 2v2" />
                  </svg>
                </button>
              </div>
            </div>
            <div
              v-else
              class="aspect-[4/1] rounded-lg border border-dashed border-slate-200 flex items-center justify-center text-sm text-slate-400"
            >
              No photos yet. Upload your first one above.
            </div>
          </div>

          <!-- Team summary -->
          <div class="bg-white rounded-xl border border-slate-200 p-6 flex items-center justify-between gap-4">
            <div>
              <h2 class="text-base font-semibold text-slate-900 tracking-tight">Team</h2>
              <p class="mt-1 text-sm text-slate-600">
                {{ shop.members.length }}
                {{ shop.members.length === 1 ? 'barber works' : 'barbers work' }} at this shop.
              </p>
            </div>
            <RouterLink
              :to="{ name: 'owner-barbers' }"
              class="inline-flex items-center gap-1.5 h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors flex-shrink-0"
            >
              Manage barbers
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </RouterLink>
          </div>
        </div>
      </template>
    </section>
  </OwnerLayout>
</template>
