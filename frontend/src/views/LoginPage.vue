<script setup lang="ts">
import { RouterLink } from 'vue-router'
import LoginForm from '@/components/auth/LoginForm.vue'
</script>

<template>
  <div class="min-h-screen bg-white flex flex-col">
    <!-- Minimal top bar -->
    <header class="border-b border-slate-200">
      <div class="max-w-7xl mx-auto flex items-center justify-between px-5 md:px-8 lg:px-12 h-16">
        <RouterLink
          to="/customer/explore"
          class="text-lg font-bold text-slate-900 tracking-tight"
        >
          IBook
        </RouterLink>
        <RouterLink
          to="/customer/explore"
          class="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 hover:bg-slate-50 transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
        >
          <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
          All barbershops
        </RouterLink>
      </div>
    </header>

    <!-- Content -->
    <main class="flex-1 flex items-start justify-center px-5 md:px-8 pt-10 md:pt-16 pb-16">
      <div class="w-full max-w-md">
        <!-- Heading -->
        <div class="mb-8">
          <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
            Welcome back
          </h1>
          <p class="mt-2 text-[15px] text-slate-600 leading-relaxed">
            Sign in to continue booking your next appointment.
          </p>
        </div>

        <!-- Form -->
        <LoginForm />

        <!-- Register links -->
        <div class="mt-8 pt-6 border-t border-slate-200 text-sm text-slate-600 space-y-2">
          <p>
            New to IBook?
            <RouterLink
              to="/register/customer"
              class="ml-1 font-semibold text-slate-900 hover:underline underline-offset-4 decoration-2"
            >
              Create a customer account
            </RouterLink>
          </p>
          <p>
            Barber or shop owner?
            <RouterLink
              to="/register/professional"
              class="ml-1 font-semibold text-slate-900 hover:underline underline-offset-4 decoration-2"
            >
              Join as a professional
            </RouterLink>
          </p>
        </div>
      </div>
    </main>
  </div>
</template>
