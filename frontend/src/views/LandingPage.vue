<script setup lang="ts">
import { RouterLink } from 'vue-router'
// Auth redirect is handled by the router guard
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col">
    <!-- Top bar -->
    <header class="border-b border-slate-200">
      <div class="max-w-7xl mx-auto flex items-center justify-between px-5 md:px-8 lg:px-12 h-16">
        <div class="flex items-center gap-2">
          <span class="inline-flex items-center justify-center h-8 w-8 rounded-md bg-slate-900 text-white text-sm font-bold">i</span>
          <span class="text-lg font-semibold text-slate-900 tracking-tight">IBook</span>
        </div>
        <RouterLink
          to="/login"
          class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 hover:bg-slate-50 transition-colors"
        >
          Log in
        </RouterLink>
      </div>
    </header>

    <!-- Hero -->
    <main class="flex-1 flex flex-col items-center justify-center px-5 md:px-8 text-center py-16 md:py-24">
      <h1 class="text-4xl md:text-6xl font-bold text-slate-900 tracking-tight leading-[1.05] max-w-3xl">
        Book your next haircut in minutes.
      </h1>
      <p class="mt-5 text-base md:text-lg text-slate-600 max-w-xl leading-relaxed">
        Find great barbers near you, see real availability, and reserve a chair online — no calls or waiting.
      </p>

      <div class="mt-9 flex flex-col sm:flex-row gap-3 w-full max-w-md">
        <RouterLink
          to="/register/customer"
          class="flex-1 inline-flex items-center justify-center gap-1.5 h-11 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
        >
          I'm a customer
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </RouterLink>
        <RouterLink
          to="/register/professional"
          class="flex-1 inline-flex items-center justify-center h-11 px-5 rounded-lg border border-slate-200 bg-white text-sm font-semibold text-slate-900 hover:border-slate-400 hover:bg-slate-50 transition-colors"
        >
          I'm a barber or shop owner
        </RouterLink>
      </div>
    </main>

    <!-- Footer -->
    <footer class="border-t border-slate-200">
      <div class="max-w-7xl mx-auto px-5 md:px-8 lg:px-12 py-6 flex items-center justify-between text-sm text-slate-500">
        <p>© {{ new Date().getFullYear() }} IBook</p>
        <p>Made in Tashkent.</p>
      </div>
    </footer>
  </div>
</template>
