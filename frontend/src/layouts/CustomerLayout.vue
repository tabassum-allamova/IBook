<script setup lang="ts">
import Navbar from '@/components/layout/Navbar.vue'
import BottomNav from '@/components/layout/BottomNav.vue'

const mobileNavItems = [
  { label: 'Explore', to: '/customer/explore', icon: 'explore' },
  { label: 'Bookings', to: '/customer/appointments', icon: 'bookings' },
  { label: 'Profile', to: '/customer/settings', icon: 'profile' },
]
</script>

<template>
  <div class="min-h-screen bg-ibook-cream flex flex-col">
    <Navbar />
    <main class="flex-1 pb-16 md:pb-0">
      <slot />
    </main>
    <BottomNav :items="mobileNavItems" />
  </div>
</template>
