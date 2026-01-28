<script setup lang="ts">
import { RouterLink } from 'vue-router'
import AuthLayout from '@/layouts/AuthLayout.vue'
import LoginForm from '@/components/auth/LoginForm.vue'
</script>

<template>
  <AuthLayout>
    <!-- Back link -->
    <div class="mb-8">
      <RouterLink
        to="/"
        class="inline-flex items-center gap-2 text-sm text-ibook-brown-500 hover:text-ibook-brown-700 transition-colors"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="2"
        >
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
        </svg>
        Back to home
      </RouterLink>
    </div>

    <!-- Heading -->
    <div class="mb-8">
      <div class="flex items-center gap-3 mb-4">
        <span class="text-2xl font-black text-ibook-brown-800">IBook</span>
      </div>
      <h1 class="text-3xl font-bold text-ibook-brown-900">Welcome back</h1>
      <p class="mt-1 text-ibook-brown-500">Sign in to your account to continue.</p>
    </div>

    <LoginForm />

    <!-- Register links -->
    <div class="mt-6 text-center space-y-2">
      <p class="text-sm text-ibook-brown-500">
        New customer?
        <RouterLink
          to="/register/customer"
          class="font-semibold text-ibook-brown-700 hover:text-ibook-brown-900 transition-colors"
        >
          Create an account
        </RouterLink>
      </p>
      <p class="text-sm text-ibook-brown-500">
        Barber or shop owner?
        <RouterLink
          to="/register/professional"
          class="font-semibold text-ibook-brown-700 hover:text-ibook-brown-900 transition-colors"
        >
          Join as a professional
        </RouterLink>
      </p>
    </div>
  </AuthLayout>
</template>
