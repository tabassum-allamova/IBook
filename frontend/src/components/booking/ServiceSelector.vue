<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useQuery } from '@tanstack/vue-query'
import api from '@/lib/axios'

const { t } = useI18n()

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
    <div v-if="isLoading" class="py-8 text-center text-slate-400 text-sm">
      {{ t('booking.services_.loading') }}
    </div>

    <!-- Services list -->
    <div v-else-if="services && services.length > 0" class="space-y-2.5">
      <label
        v-for="svc in services"
        :key="svc.id"
        class="flex items-center gap-3 p-4 rounded-xl border cursor-pointer transition-colors bg-white"
        :class="
          selectedIds.has(svc.id)
            ? 'border-slate-900 ring-2 ring-slate-900/10'
            : 'border-slate-200 hover:border-slate-400'
        "
      >
        <input
          type="checkbox"
          :checked="selectedIds.has(svc.id)"
          class="w-4 h-4 accent-slate-900"
          @change="toggle(svc.id)"
        />
        <div class="flex-1 min-w-0">
          <div class="font-medium text-slate-900">{{ svc.name }}</div>
          <div class="text-sm text-slate-500 mt-0.5">
            {{ svc.duration_minutes }} {{ t('booking.summary.minutes') }}
          </div>
        </div>
        <div class="text-sm font-semibold text-slate-900 tabular-nums">
          {{ formatPrice(svc.price) }}
        </div>
      </label>
    </div>

    <!-- Empty state -->
    <div v-else class="py-8 text-center text-slate-400 text-sm">
      {{ t('booking.services_.empty') }}
    </div>
  </div>
</template>
