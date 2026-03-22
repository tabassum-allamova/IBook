<script setup lang="ts">
import CustomerLayout from '@/layouts/CustomerLayout.vue'

defineProps<{
  shopId: string
}>()
</script>

<template>
  <CustomerLayout>
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <h1 class="text-2xl font-bold text-ibook-brown-900 mb-4">Shop Detail</h1>
      <p class="text-ibook-brown-500">Coming soon — shop detail page (Plan 03).</p>
    </div>
  </CustomerLayout>
</template>
