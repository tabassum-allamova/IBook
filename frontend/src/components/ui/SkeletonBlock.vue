<template>
  <div
    class="animate-pulse rounded-lg bg-slate-100"
    :class="className"
    :style="{ height, width }"
  />
</template>

<script setup lang="ts">
defineProps<{
  height?: string
  width?: string
  className?: string
}>()
</script>
