<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import Sidebar from '@/components/layout/Sidebar.vue'
import BottomNav from '@/components/layout/BottomNav.vue'

const { t } = useI18n()

const navItems = computed(() => [
  { label: t('nav.overview'), to: '/owner/overview' },
  { label: t('nav.shops'), to: '/owner/shop' },
  { label: t('nav.barbers'), to: '/owner/barbers' },
  { label: t('nav.analytics'), to: '/owner/analytics' },
  { label: t('nav.settings'), to: '/owner/settings' },
])

const mobileNavItems = computed(() => [
  { label: t('nav.overview'), to: '/owner/overview', icon: 'analytics' },
  { label: t('nav.shops'), to: '/owner/shop', icon: 'shop' },
  { label: t('nav.analytics'), to: '/owner/analytics', icon: 'analytics' },
  { label: t('nav.settings'), to: '/owner/settings', icon: 'settings' },
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
