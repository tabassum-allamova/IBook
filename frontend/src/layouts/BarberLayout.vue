<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'

const navItems = [
  { label: 'Analytics', to: '/barber/dashboard' },
  { label: 'Appointments', to: '/barber/appointments' },
  { label: 'Profile', to: '/barber/profile' },
  { label: 'Services', to: '/barber/services' },
  { label: 'Availability', to: '/barber/availability' },
  { label: 'Settings', to: '/barber/settings' },
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
