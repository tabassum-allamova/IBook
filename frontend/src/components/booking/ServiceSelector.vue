<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import api from '@/lib/axios'

export interface Service {
  id: number
  name: string
  price: number
  duration_minutes: number
}

const props = defineProps<{
  barberId: number
}>()

const emit = defineEmits<{
  update: [services: Service[]]
}>()

const selectedIds = ref<Set<number>>(new Set())

const { data: services, isLoading } = useQuery<Service[]>({
  queryKey: computed(() => ['barber-services', props.barberId]),
  queryFn: () =>
    api
      .get<Service[]>('/api/bookings/barber-services/', {
        params: { barber_id: props.barberId },
      })
      .then((r) => r.data),
})

const selectedServices = computed(() => {
  if (!services.value) return []
  return services.value.filter((s) => selectedIds.value.has(s.id))
})

const totalPrice = computed(() =>
  selectedServices.value.reduce((sum, s) => sum + s.price, 0),
)

const totalDuration = computed(() =>
  selectedServices.value.reduce((sum, s) => sum + s.duration_minutes, 0),
)

function toggle(id: number) {
  const next = new Set(selectedIds.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  selectedIds.value = next
}

function formatPrice(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

// Pre-select services passed via query params (reschedule flow)
function preselectServices(ids: number[]) {
  selectedIds.value = new Set(ids)
}

defineExpose({ preselectServices })

watch(selectedServices, (val) => {
  emit('update', val)
})
</script>

<template>
  <div>
    <!-- Loading state -->
    <div v-if="isLoading" class="py-8 text-center text-ibook-brown-400 text-sm">
      Loading services...
    </div>

    <!-- Services list -->
    <div v-else-if="services && services.length > 0" class="space-y-3">
      <label
        v-for="svc in services"
        :key="svc.id"
        class="flex items-center gap-3 p-3 rounded-xl border cursor-pointer transition-colors"
        :class="
          selectedIds.has(svc.id)
            ? 'border-ibook-gold-400 bg-ibook-brown-50'
            : 'border-ibook-brown-200 bg-white hover:border-ibook-brown-400'
        "
      >
        <input
          type="checkbox"
          :checked="selectedIds.has(svc.id)"
          class="w-4 h-4 accent-ibook-gold-500"
          @change="toggle(svc.id)"
        />
        <div class="flex-1 min-w-0">
          <div class="font-medium text-ibook-brown-800">{{ svc.name }}</div>
          <div class="text-sm text-ibook-brown-400">
            {{ svc.duration_minutes }} min
          </div>
        </div>
        <div class="text-sm font-semibold text-ibook-brown-700">
          {{ formatPrice(svc.price) }}
        </div>
      </label>

      <!-- Summary bar -->
      <div
        v-if="selectedServices.length > 0"
        class="mt-4 p-3 rounded-xl bg-ibook-brown-800 text-white text-sm flex items-center justify-between"
      >
        <span>{{ selectedServices.length }} service{{ selectedServices.length > 1 ? 's' : '' }} selected</span>
        <span>
          Total: {{ formatPrice(totalPrice) }} &middot; {{ totalDuration }} min
        </span>
      </div>
    </div>

    <!-- Empty state -->
    <div v-else class="py-8 text-center text-ibook-brown-400 text-sm">
      No services available for this barber
    </div>
  </div>
</template>
