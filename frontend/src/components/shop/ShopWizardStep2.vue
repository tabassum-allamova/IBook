<script setup lang="ts">
interface HoursEntry {
  day_of_week: number
  is_open: boolean
  opens_at: string
  closes_at: string
  break_start: string
  break_end: string
}

interface ShopForm {
  hours: HoursEntry[]
}

const props = defineProps<{
  modelValue: ShopForm
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ShopForm]
}>()

const DAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

function updateHours(index: number, field: keyof HoursEntry, value: boolean | string) {
  const newHours = props.modelValue.hours.map((entry, i) =>
    i === index ? { ...entry, [field]: value } : entry,
  )
  emit('update:modelValue', { ...props.modelValue, hours: newHours })
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-ibook-brown-700 mb-1">Operating Hours</h2>
      <p class="text-sm text-ibook-brown-400">Set your shop's weekly schedule</p>
    </div>

    <div class="space-y-3">
      <div
        v-for="(entry, index) in modelValue.hours"
        :key="entry.day_of_week"
        class="flex items-start gap-4 p-3 rounded-lg border"
        :class="entry.is_open ? 'border-ibook-brown-200 bg-white' : 'border-ibook-brown-100 bg-ibook-brown-50'"
      >
        <!-- Day toggle -->
        <div class="flex items-center gap-2 min-w-[80px] pt-1">
          <input
            type="checkbox"
            :id="`day-${index}`"
            :checked="entry.is_open"
            @change="updateHours(index, 'is_open', ($event.target as HTMLInputElement).checked)"
            class="w-4 h-4 accent-ibook-gold-500 cursor-pointer"
          />
          <label
            :for="`day-${index}`"
            class="text-sm font-medium cursor-pointer"
            :class="entry.is_open ? 'text-ibook-brown-700' : 'text-ibook-brown-400'"
          >
            {{ DAY_LABELS[index] }}
          </label>
        </div>

        <!-- Time inputs when open -->
        <div v-if="entry.is_open" class="flex-1 space-y-2">
          <!-- Open / Close times -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs text-ibook-brown-400 w-14">Open</span>
            <input
              type="time"
              :value="entry.opens_at"
              @change="updateHours(index, 'opens_at', ($event.target as HTMLInputElement).value)"
              class="px-2 py-1 border border-ibook-brown-200 rounded text-sm text-ibook-brown-700 focus:outline-none focus:ring-2 focus:ring-ibook-gold-500"
            />
            <span class="text-xs text-ibook-brown-400">to</span>
            <input
              type="time"
              :value="entry.closes_at"
              @change="updateHours(index, 'closes_at', ($event.target as HTMLInputElement).value)"
              class="px-2 py-1 border border-ibook-brown-200 rounded text-sm text-ibook-brown-700 focus:outline-none focus:ring-2 focus:ring-ibook-gold-500"
            />
          </div>
          <!-- Break times -->
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-xs text-ibook-brown-400 w-14">Break</span>
            <input
              type="time"
              :value="entry.break_start"
              @change="updateHours(index, 'break_start', ($event.target as HTMLInputElement).value)"
              class="px-2 py-1 border border-ibook-brown-200 rounded text-sm text-ibook-brown-700 focus:outline-none focus:ring-2 focus:ring-ibook-gold-500"
            />
            <span class="text-xs text-ibook-brown-400">to</span>
            <input
              type="time"
              :value="entry.break_end"
              @change="updateHours(index, 'break_end', ($event.target as HTMLInputElement).value)"
              class="px-2 py-1 border border-ibook-brown-200 rounded text-sm text-ibook-brown-700 focus:outline-none focus:ring-2 focus:ring-ibook-gold-500"
            />
          </div>
        </div>

        <!-- Closed state -->
        <div v-else class="flex-1 pt-1">
          <span class="text-sm text-ibook-brown-400">Closed</span>
        </div>
      </div>
    </div>
  </div>
</template>
