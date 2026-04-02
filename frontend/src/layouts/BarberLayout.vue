<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'
import BottomNav from '@/components/layout/BottomNav.vue'

const navItems = [
  { label: 'Analytics', to: '/barber/dashboard' },
  { label: 'Appointments', to: '/barber/appointments' },
  { label: 'Profile', to: '/barber/profile' },
  { label: 'Services', to: '/barber/services' },
  { label: 'Availability', to: '/barber/availability' },
  { label: 'Settings', to: '/barber/settings' },
]

const mobileNavItems = [
  { label: 'Appointments', to: '/barber/appointments', icon: 'appointments' },
  { label: 'Services', to: '/barber/services', icon: 'services' },
  { label: 'Analytics', to: '/barber/dashboard', icon: 'analytics' },
]
</script>

<template>
  <div class="min-h-screen md:h-screen bg-ibook-cream flex flex-col md:flex-row md:overflow-hidden">
    <Sidebar class="hidden md:block" :nav-items="navItems" />
    <main class="flex-1 overflow-y-auto p-8 pb-20 md:pb-8">
      <slot />
    </main>
    <BottomNav :items="mobileNavItems" />
  </div>
</template>
