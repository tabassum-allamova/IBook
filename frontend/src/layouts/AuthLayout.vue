<script setup lang="ts">
// Split-screen auth layout: form slot on left, hero on right
</script>

<template>
  <div class="min-h-screen flex">
    <!-- Left: form panel -->
    <div class="flex-1 flex flex-col justify-center items-center bg-white px-8 py-12 lg:px-16">
      <div class="w-full max-w-md">
        <slot />
      </div>
    </div>

    <!-- Right: hero panel -->
    <div
      class="hidden lg:flex flex-1 flex-col justify-center items-center bg-ibook-brown-800 px-12 py-16 relative overflow-hidden"
    >
      <!-- Decorative circles -->
      <div
        class="absolute top-[-60px] right-[-60px] w-64 h-64 rounded-full bg-ibook-brown-700 opacity-40"
      ></div>
      <div
        class="absolute bottom-[-80px] left-[-40px] w-80 h-80 rounded-full bg-ibook-brown-900 opacity-30"
      ></div>

      <div class="relative z-10 text-center">
        <div class="mb-6">
          <span
            class="text-5xl font-black tracking-tight text-ibook-gold-400"
          >IBook</span>
        </div>
        <h2 class="text-2xl font-semibold text-ibook-brown-100 mb-4 leading-snug">
          Your Perfect Cut,<br />Always on Time
        </h2>
        <p class="text-ibook-brown-300 text-base max-w-xs mx-auto leading-relaxed">
          Connect with top barbers in your area. Book appointments in seconds, manage your schedule effortlessly.
        </p>

        <!-- Decorative scissors icon -->
        <div class="mt-10 flex justify-center gap-3">
          <div class="w-2 h-2 rounded-full bg-ibook-gold-400 opacity-70"></div>
          <div class="w-2 h-2 rounded-full bg-ibook-gold-400 opacity-50"></div>
          <div class="w-2 h-2 rounded-full bg-ibook-gold-400 opacity-30"></div>
        </div>
      </div>
    </div>
  </div>
</template>
