<script setup lang="ts">
import OwnerLayout from '@/layouts/OwnerLayout.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <OwnerLayout>
    <div class="p-8">
      <!-- Page header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-ibook-brown-900">Shop Overview</h1>
        <p class="mt-1 text-ibook-brown-500">
          Welcome back, {{ auth.user?.fullName }}. Here's how your shop is performing.
        </p>
      </div>

      <!-- Stats row -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">Total Bookings</p>
          <p class="text-3xl font-bold text-ibook-brown-900">0</p>
          <p class="text-xs text-ibook-brown-400 mt-1">all time</p>
        </div>
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">Active Barbers</p>
          <p class="text-3xl font-bold text-ibook-brown-900">0</p>
          <p class="text-xs text-ibook-brown-400 mt-1">in your shop</p>
        </div>
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">Today's Revenue</p>
          <p class="text-3xl font-bold text-ibook-gold-500">$0</p>
          <p class="text-xs text-ibook-brown-400 mt-1">estimated</p>
        </div>
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">Avg. Rating</p>
          <p class="text-3xl font-bold text-ibook-brown-900">—</p>
          <p class="text-xs text-ibook-brown-400 mt-1">from reviews</p>
        </div>
      </div>

      <!-- Placeholder table -->
      <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-ibook-brown-100">
          <h2 class="text-lg font-semibold text-ibook-brown-800">Recent Bookings</h2>
        </div>
        <div class="p-12 flex flex-col items-center text-center">
          <div
            class="w-16 h-16 rounded-full bg-ibook-brown-100 flex items-center justify-center mb-4"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-8 w-8 text-ibook-brown-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              stroke-width="1.5"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <h3 class="text-lg font-semibold text-ibook-brown-800 mb-2">No data yet</h3>
          <p class="text-ibook-brown-500 text-sm max-w-xs">
            Analytics and booking data will appear here once your shop starts receiving appointments.
          </p>
        </div>
      </div>
    </div>
  </OwnerLayout>
</template>
