<script setup lang="ts">
import BarberLayout from '@/layouts/BarberLayout.vue'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <BarberLayout>
    <div class="p-8">
      <!-- Page header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-ibook-brown-900">Your Appointments</h1>
        <p class="mt-1 text-ibook-brown-500">
          Welcome back, {{ auth.user?.fullName }}. Here are your upcoming appointments.
        </p>
      </div>

      <!-- Stats row -->
      <div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">Today</p>
          <p class="text-3xl font-bold text-ibook-brown-900">0</p>
          <p class="text-xs text-ibook-brown-400 mt-1">appointments</p>
        </div>
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">This Week</p>
          <p class="text-3xl font-bold text-ibook-brown-900">0</p>
          <p class="text-xs text-ibook-brown-400 mt-1">appointments</p>
        </div>
        <div class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-5">
          <p class="text-sm font-medium text-ibook-brown-500 mb-1">Total</p>
          <p class="text-3xl font-bold text-ibook-gold-500">0</p>
          <p class="text-xs text-ibook-brown-400 mt-1">all time</p>
        </div>
      </div>

      <!-- Empty state -->
      <div
        class="bg-white rounded-2xl border border-ibook-brown-100 shadow-sm p-12 flex flex-col items-center text-center"
      >
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
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
        <h3 class="text-lg font-semibold text-ibook-brown-800 mb-2">No appointments yet</h3>
        <p class="text-ibook-brown-500 text-sm max-w-xs">
          Once customers start booking with you, their appointments will appear here.
        </p>
      </div>
    </div>
  </BarberLayout>
</template>
