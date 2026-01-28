<script setup lang="ts">
import { RouterLink } from 'vue-router'
// Auth redirect is handled by the router guard
</script>

<template>
  <div class="min-h-screen bg-ibook-cream flex flex-col">
    <!-- Top bar -->
    <header class="px-6 py-4 flex justify-end">
      <RouterLink
        to="/login"
        class="text-sm font-medium text-ibook-brown-600 hover:text-ibook-brown-800 transition-colors"
      >
        Already have an account? Log in →
      </RouterLink>
    </header>

    <!-- Hero -->
    <main class="flex-1 flex flex-col items-center justify-center px-6 text-center">
      <!-- Logo mark -->
      <div class="mb-8">
        <div
          class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-ibook-brown-800 shadow-xl mb-5"
        >
          <span class="text-3xl font-black text-ibook-gold-400">IB</span>
        </div>
        <h1 class="text-5xl sm:text-6xl font-black tracking-tight text-ibook-brown-900">
          IBook
        </h1>
      </div>

      <p class="text-xl sm:text-2xl text-ibook-brown-600 font-medium mb-3 max-w-md leading-snug">
        Book your perfect cut, anywhere.
      </p>
      <p class="text-ibook-brown-400 text-base mb-12 max-w-sm">
        Connect with top barbers in your area and manage your appointments effortlessly.
      </p>

      <!-- CTA buttons -->
      <div class="flex flex-col sm:flex-row gap-4 w-full max-w-sm">
        <RouterLink
          to="/register/customer"
          class="flex-1 py-4 px-6 bg-ibook-brown-800 hover:bg-ibook-brown-700 text-white font-semibold rounded-xl text-center transition-colors shadow-md"
        >
          I'm a Customer
        </RouterLink>
        <RouterLink
          to="/register/professional"
          class="flex-1 py-4 px-6 bg-white hover:bg-ibook-brown-50 text-ibook-brown-800 font-semibold rounded-xl text-center transition-colors shadow-md border-2 border-ibook-brown-200 hover:border-ibook-brown-400"
        >
          I'm a Barber / Shop Owner
        </RouterLink>
      </div>

      <!-- Decorative dots -->
      <div class="mt-16 flex gap-2">
        <div class="w-1.5 h-1.5 rounded-full bg-ibook-brown-300"></div>
        <div class="w-1.5 h-1.5 rounded-full bg-ibook-gold-400"></div>
        <div class="w-1.5 h-1.5 rounded-full bg-ibook-brown-300"></div>
      </div>
    </main>

    <!-- Footer -->
    <footer class="px-6 py-4 text-center">
      <p class="text-xs text-ibook-brown-400">
        © {{ new Date().getFullYear() }} IBook. All rights reserved.
      </p>
    </footer>
  </div>
</template>
