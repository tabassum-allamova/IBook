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
  return amount.toLocaleString('uz-UZ') + ' UZS'
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
  <div>
    <!-- Empty state -->
    <div
      v-if="localServices.length === 0"
      class="py-12 flex flex-col items-center text-center text-ibook-brown-400"
    >
      <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mb-3 text-ibook-brown-200" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
      <p class="text-sm font-medium">No services yet — add your first service</p>
    </div>

    <!-- Draggable list -->
    <draggable
      v-else
      v-model="localServices"
      item-key="id"
      handle=".drag-handle"
      class="space-y-2"
      @end="onDragEnd"
    >
      <template #item="{ element }">
        <div
          class="flex items-center gap-3 bg-white rounded-xl border border-ibook-brown-100 px-4 py-3 shadow-sm hover:shadow transition-shadow"
        >
          <!-- Drag handle -->
          <span
            class="drag-handle cursor-grab text-ibook-brown-300 hover:text-ibook-brown-500 text-xl leading-none select-none flex-shrink-0"
            title="Drag to reorder"
          >
            ⠿
          </span>

          <!-- Service info -->
          <div class="flex-1 min-w-0">
            <p class="text-sm font-semibold text-ibook-brown-900 truncate">{{ element.name }}</p>
            <p class="text-xs text-ibook-brown-400 mt-0.5">{{ element.duration_minutes }} min</p>
          </div>

          <!-- Price -->
          <span class="text-sm font-medium text-ibook-brown-700 flex-shrink-0">
            {{ formatUZS(element.price) }}
          </span>

          <!-- Edit button -->
          <button
            type="button"
            class="flex-shrink-0 p-1.5 rounded-lg text-ibook-brown-400 hover:text-ibook-brown-700 hover:bg-ibook-brown-100 transition-colors cursor-pointer"
            title="Edit service"
            @click="emit('edit', element)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
            </svg>
          </button>
        </div>
      </template>
    </draggable>
  </div>
</template>
