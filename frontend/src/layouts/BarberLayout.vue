<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'

const navItems = [
  { label: 'Appointments', to: '/barber/dashboard' },
  { label: 'Availability', to: '/barber/availability' },
  { label: 'Settings', to: '/barber/settings' },
]
</script>

<template>
  <div class="min-h-screen bg-ibook-cream flex">
    <Sidebar :nav-items="navItems" />
    <main class="flex-1 overflow-auto">
      <slot />
    </main>
  </div>
</template>
