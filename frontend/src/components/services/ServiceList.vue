<script setup lang="ts">
import { ref, watch } from 'vue'
import draggable from 'vuedraggable'
import { useMutation } from '@tanstack/vue-query'
import api from '@/lib/axios'
import type { Service } from './ServiceModal.vue'

const props = defineProps<{
  services: Service[]
}>()

const emit = defineEmits<{
  edit: [service: Service]
  reordered: []
}>()

const localServices = ref<Service[]>([])

watch(
  () => props.services,
  (newServices) => {
    localServices.value = newServices.map((s) => ({ ...s }))
  },
  { immediate: true, deep: true },
)

function formatUZS(amount: number): string {
  return amount.toLocaleString('en-US') + ' UZS'
}

const reorderMutation = useMutation({
  mutationFn: async (order: Array<{ id: number; sort_order: number }>) => {
    await api.patch('/api/services/reorder/', order)
  },
})

async function onDragEnd() {
  const order = localServices.value.map((s, i) => ({ id: s.id, sort_order: i }))
  await reorderMutation.mutateAsync(order)
  emit('reordered')
}
</script>

<template>
  <div class="max-w-3xl rounded-xl border border-slate-200 bg-white overflow-hidden">
    <draggable
      v-model="localServices"
      item-key="id"
      handle=".drag-handle"
      class="divide-y divide-slate-100"
      @end="onDragEnd"
    >
      <template #item="{ element }">
        <div class="flex items-center gap-3 px-5 py-4 hover:bg-slate-50/60 transition-colors">
          <!-- Drag handle -->
          <span
            class="drag-handle cursor-grab text-slate-300 hover:text-slate-500 select-none flex-shrink-0"
            title="Drag to reorder"
            aria-hidden="true"
          >
            <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4 8h16M4 16h16" />
            </svg>
          </span>

          <!-- Service info -->
          <div class="flex-1 min-w-0">
            <p class="text-base font-semibold text-slate-900 truncate">{{ element.name }}</p>
            <p class="text-sm text-slate-500 mt-0.5">{{ element.duration_minutes }} min</p>
          </div>

          <!-- Price -->
          <span class="text-sm font-semibold text-slate-900 tabular-nums flex-shrink-0">
            {{ formatUZS(element.price) }}
          </span>

          <!-- Edit button -->
          <button
            type="button"
            class="flex-shrink-0 inline-flex items-center justify-center h-9 w-9 rounded-lg text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
            title="Edit service"
            aria-label="Edit service"
            @click="emit('edit', element)"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        </div>
      </template>
    </draggable>
  </div>
</template>
