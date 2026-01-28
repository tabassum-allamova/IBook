<script setup lang="ts">
import CustomerLayout from '@/layouts/CustomerLayout.vue'
</script>

<template>
  <CustomerLayout>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <!-- Page header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-ibook-brown-900">Explore Barbers</h1>
        <p class="mt-1 text-ibook-brown-500">Find and book the perfect barber near you.</p>
      </div>

      <!-- Placeholder content -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="n in 6"
          :key="n"
          class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm overflow-hidden hover:shadow-md transition-shadow"
        >
          <!-- Avatar placeholder -->
          <div class="h-48 bg-ibook-brown-100 flex items-center justify-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-16 w-16 text-ibook-brown-300"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <div class="p-5">
            <div class="h-4 bg-ibook-brown-100 rounded mb-2 w-3/4"></div>
            <div class="h-3 bg-ibook-brown-50 rounded mb-4 w-1/2"></div>
            <button
              class="w-full py-2 px-4 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white text-sm font-semibold rounded-lg transition-colors cursor-pointer"
            >
              Book Now
            </button>
          </div>
        </div>
      </div>

      <p class="mt-10 text-center text-ibook-brown-400 text-sm">
        Barber listings coming soon. Stay tuned!
      </p>
    </div>
  </CustomerLayout>
</template>
