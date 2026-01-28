<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'

const navItems = [
  { label: 'Shop Overview', to: '/owner/overview' },
  { label: 'Barbers', to: '/owner/barbers' },
  { label: 'Analytics', to: '/owner/analytics' },
  { label: 'Settings', to: '/owner/settings' },
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
