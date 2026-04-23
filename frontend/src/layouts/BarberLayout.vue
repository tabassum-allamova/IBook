<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Sidebar from '@/components/layout/Sidebar.vue'
import BottomNav from '@/components/layout/BottomNav.vue'

const { t } = useI18n()

const navItems = computed(() => [
  { label: t('nav.analytics'), to: '/barber/dashboard' },
  { label: t('nav.appointments'), to: '/barber/appointments' },
  { label: t('nav.services'), to: '/barber/services' },
  { label: t('nav.availability'), to: '/barber/availability' },
  { label: t('nav.settings'), to: '/barber/settings' },
])

const mobileNavItems = computed(() => [
  { label: t('nav.appointments'), to: '/barber/appointments', icon: 'appointments' },
  { label: t('nav.services'), to: '/barber/services', icon: 'services' },
  { label: t('nav.analytics'), to: '/barber/dashboard', icon: 'analytics' },
])
</script>

<template>
  <div class="min-h-screen md:h-screen bg-slate-50 flex flex-col md:flex-row md:overflow-hidden">
    <Sidebar class="hidden md:block" :nav-items="navItems" />
    <main class="flex-1 overflow-y-auto p-6 md:p-8 pb-20 md:pb-8">
      <slot />
    </main>
    <BottomNav :items="mobileNavItems" />
  </div>
</template>
