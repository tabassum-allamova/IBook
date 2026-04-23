<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import CustomerRegisterForm from '@/components/auth/CustomerRegisterForm.vue'

const success = ref(false)
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
        <!-- Success state -->
        <template v-if="success">
          <div class="text-center py-6">
            <div
              class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-emerald-50 border border-emerald-100 mb-5"
            >
              <svg
                class="h-7 w-7 text-emerald-600"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                stroke-width="2"
              >
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight mb-2">
              Check your email
            </h2>
            <p class="text-[15px] text-slate-600 leading-relaxed mb-6 max-w-sm mx-auto">
              We've sent a verification link to your email. Click it to activate your account.
            </p>
            <RouterLink
              to="/login"
              class="inline-flex items-center justify-center gap-1 h-11 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-slate-900 focus:ring-offset-2"
            >
              Go to sign in
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </RouterLink>
          </div>
        </template>

        <!-- Registration form -->
        <template v-else>
          <!-- Heading -->
          <div class="mb-8">
            <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
              Create your account
            </h1>
            <p class="mt-2 text-[15px] text-slate-600 leading-relaxed">
              Join IBook and book your next cut in seconds.
            </p>
          </div>

          <CustomerRegisterForm @success="success = true" />

          <!-- Login link -->
          <div class="mt-8 pt-6 border-t border-slate-200 text-sm text-slate-600">
            <p>
              Already have an account?
              <RouterLink
                to="/login"
                class="ml-1 font-semibold text-slate-900 hover:underline underline-offset-4 decoration-2"
              >
                Sign in
              </RouterLink>
            </p>
          </div>
        </template>
      </div>
    </main>
  </div>
</template>
