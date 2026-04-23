<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

const props = defineProps<{
  slots: string[]
  selected: string
  loading: boolean
}>()

const emit = defineEmits<{
  select: [slot: string]
}>()

interface SlotGroup {
  label: string
  slots: string[]
}

const groupedSlots = computed<SlotGroup[]>(() => {
  const morning: string[] = []
  const afternoon: string[] = []
  const evening: string[] = []
  for (const s of props.slots) {
    const h = parseInt(s.split(':')[0] ?? '0', 10)
    if (h < 12) morning.push(s)
    else if (h < 17) afternoon.push(s)
    else evening.push(s)
  }
  const out: SlotGroup[] = []
  if (morning.length) out.push({ label: t('booking.slotGrid.morning'), slots: morning })
  if (afternoon.length) out.push({ label: t('booking.slotGrid.afternoon'), slots: afternoon })
  if (evening.length) out.push({ label: t('booking.slotGrid.evening'), slots: evening })
  return out
})
</script>

<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="py-10 text-center">
      <p class="text-slate-500 text-sm">{{ t('booking.slotGrid.loading') }}</p>
    </div>

    <!-- Empty -->
    <div
      v-else-if="slots.length === 0"
      class="py-12 px-6 text-center border border-dashed border-slate-200 rounded-xl bg-slate-50"
    >
      <p class="text-base font-semibold text-slate-900 mb-1">
        {{ t('booking.slotGrid.empty') }}
      </p>
      <p class="text-sm text-slate-500">{{ t('booking.slotGrid.emptyHint') }}</p>
    </div>

    <!-- Grouped slots -->
    <div v-else class="space-y-7">
      <section v-for="group in groupedSlots" :key="group.label">
        <h3 class="text-sm font-medium text-slate-500 mb-3">{{ group.label }}</h3>
        <div class="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-2">
          <button
            v-for="slot in group.slots"
            :key="slot"
            type="button"
            class="h-10 rounded-lg text-sm font-medium tabular-nums transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
            :class="
              slot === selected
                ? 'bg-slate-900 text-white'
                : 'bg-white border border-slate-200 text-slate-700 hover:border-slate-900 hover:text-slate-900'
            "
            @click="emit('select', slot)"
          >
            {{ slot }}
          </button>
        </div>
      </section>
    </div>
  </div>
</template>
