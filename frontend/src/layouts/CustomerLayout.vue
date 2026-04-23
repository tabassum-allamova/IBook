<script setup lang="ts">
import { computed } from 'vue'
import Navbar from '@/components/layout/Navbar.vue'
import BottomNav from '@/components/layout/BottomNav.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const mobileNavItems = computed(() => {
  const exploreItem = { label: 'Explore', to: '/customer/explore', icon: 'explore' }
  if (auth.isAuthenticated && auth.user?.role === 'CUSTOMER') {
    return [
      exploreItem,
      { label: 'Bookings', to: '/customer/appointments', icon: 'bookings' },
      { label: 'Profile', to: '/customer/settings', icon: 'profile' },
    ]
  }
  return [
    exploreItem,
    { label: 'Log in', to: '/login', icon: 'profile' },
    { label: 'Sign up', to: '/register/customer', icon: 'settings' },
  ]
})
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col">
    <Navbar />
    <main class="flex-1 pb-16 md:pb-0">
      <slot />
    </main>
    <BottomNav :items="mobileNavItems" />
  </div>
</template>
