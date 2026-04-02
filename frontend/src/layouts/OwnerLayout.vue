<script setup lang="ts">
import Sidebar from '@/components/layout/Sidebar.vue'
import BottomNav from '@/components/layout/BottomNav.vue'

const navItems = [
  { label: 'Shop Overview', to: '/owner/overview' },
  { label: 'My Shop', to: '/owner/shop' },
  { label: 'Analytics', to: '/owner/analytics' },
  { label: 'Settings', to: '/owner/settings' },
]

const mobileNavItems = [
  { label: 'Overview', to: '/owner/overview', icon: 'analytics' },
  { label: 'My Shop', to: '/owner/shop', icon: 'shop' },
  { label: 'Settings', to: '/owner/settings', icon: 'settings' },
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
