<script setup lang="ts">
import { ref } from 'vue'
import { RouterLink } from 'vue-router'
import AuthLayout from '@/layouts/AuthLayout.vue'
import CustomerRegisterForm from '@/components/auth/CustomerRegisterForm.vue'

const success = ref(false)
</script>

<template>
  <AuthLayout>
    <!-- Success state -->
    <template v-if="success">
      <div class="text-center py-8">
        <div
          class="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-6"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-8 w-8 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <h2 class="text-2xl font-bold text-ibook-brown-900 mb-3">Check your email</h2>
        <p class="text-ibook-brown-500 mb-8 max-w-xs mx-auto leading-relaxed">
          We've sent a verification link to your email address. Please check your inbox to activate your account.
        </p>
        <RouterLink
          to="/login"
          class="inline-block py-3 px-8 bg-ibook-brown-700 hover:bg-ibook-brown-600 text-white font-semibold rounded-lg transition-colors"
        >
          Go to Login
        </RouterLink>
      </div>
    </template>

    <!-- Registration form -->
    <template v-else>
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
        <h1 class="text-3xl font-bold text-ibook-brown-900">Create your account</h1>
        <p class="mt-1 text-ibook-brown-500">Join IBook and book your perfect cut today.</p>
      </div>

      <CustomerRegisterForm @success="success = true" />

      <p class="mt-6 text-center text-sm text-ibook-brown-500">
        Already have an account?
        <RouterLink
          to="/login"
          class="font-semibold text-ibook-brown-700 hover:text-ibook-brown-900 transition-colors"
        >
          Sign in
        </RouterLink>
      </p>
    </template>
  </AuthLayout>
</template>
