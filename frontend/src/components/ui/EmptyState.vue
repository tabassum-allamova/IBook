<template>
  <div class="flex flex-col items-center gap-4 py-16 text-center px-6">
    <div class="w-12 h-12 text-slate-300">
      <slot name="icon">
        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
        </svg>
      </slot>
    </div>
    <h3 class="text-lg font-semibold text-slate-900 tracking-tight">{{ title }}</h3>
    <p v-if="description" class="text-sm text-slate-500 max-w-xs leading-relaxed">{{ description }}</p>
    <RouterLink
      v-if="actionTo"
      :to="actionTo"
      class="mt-2 inline-flex items-center gap-1.5 h-11 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
    >
      {{ actionLabel }}
      <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </RouterLink>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  actionTo?: string
  actionLabel?: string
}>()
</script>
