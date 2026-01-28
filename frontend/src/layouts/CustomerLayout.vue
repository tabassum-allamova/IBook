<script setup lang="ts">
import Navbar from '@/components/layout/Navbar.vue'
</script>

<template>
  <div class="min-h-screen bg-ibook-cream flex flex-col">
    <Navbar />
    <main class="flex-1">
      <slot />
    </main>
  </div>
</template>
