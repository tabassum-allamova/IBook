<script setup lang="ts">
defineProps<{
  slots: string[]
  selected: string
  loading: boolean
}>()

const emit = defineEmits<{
  select: [slot: string]
}>()
</script>

<template>
  <div>
    <!-- Loading state -->
    <div v-if="loading" class="py-8 text-center text-ibook-brown-400 text-sm">
      Loading slots...
    </div>

    <!-- Empty state -->
    <div
      v-else-if="slots.length === 0"
      class="py-8 text-center text-ibook-brown-400 text-sm"
    >
      No available slots for this date
    </div>

    <!-- Slot chips -->
    <div v-else class="flex flex-wrap gap-2">
      <button
        v-for="slot in slots"
        :key="slot"
        type="button"
        class="px-4 py-2 rounded-lg text-sm transition-colors cursor-pointer"
        :class="
          slot === selected
            ? 'bg-ibook-brown-800 text-white font-bold'
            : 'bg-white border border-ibook-brown-200 hover:border-ibook-gold-400 text-ibook-brown-700'
        "
        @click="emit('select', slot)"
      >
        {{ slot }}
      </button>
    </div>
  </div>
</template>
