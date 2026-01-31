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
  <div class="h-screen bg-ibook-cream flex overflow-hidden">
    <Sidebar :nav-items="navItems" />
    <main class="flex-1 overflow-y-auto p-8">
      <slot />
    </main>
  </div>
</template>
