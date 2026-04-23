<script setup lang="ts">
interface ShopForm {
  name: string
  address: string
  lat: string | null
  lng: string | null
  description: string
}

const props = defineProps<{
  modelValue: ShopForm
}>()

const emit = defineEmits<{
  'update:modelValue': [value: ShopForm]
}>()

function update(field: keyof ShopForm, value: string | null) {
  emit('update:modelValue', { ...props.modelValue, [field]: value })
}
</script>

<template>
  <div class="space-y-6">
    <div>
      <h2 class="text-xl font-semibold text-slate-700 mb-1">Shop Details</h2>
      <p class="text-sm text-slate-400">Enter your shop's basic information</p>
    </div>

    <!-- Shop Name -->
    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-700">
        Shop Name <span class="text-red-500">*</span>
      </label>
      <input
        type="text"
        :value="modelValue.name"
        @input="update('name', ($event.target as HTMLInputElement).value)"
        placeholder="My Barbershop"
        class="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900"
      />
    </div>

    <!-- Address -->
    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-700">
        Address <span class="text-red-500">*</span>
      </label>
      <textarea
        :value="modelValue.address"
        @input="update('address', ($event.target as HTMLTextAreaElement).value)"
        placeholder="123 Amir Temur Ave, Tashkent"
        rows="2"
        class="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 resize-none"
      />
    </div>

    <!-- Coordinates -->
    <div class="grid grid-cols-2 gap-4">
      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-700">
          Latitude <span class="text-slate-400 font-normal">(optional)</span>
        </label>
        <input
          type="number"
          step="any"
          :value="modelValue.lat ?? ''"
          @input="update('lat', ($event.target as HTMLInputElement).value || null)"
          placeholder="41.2995"
          class="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900"
        />
      </div>
      <div class="space-y-1">
        <label class="block text-sm font-medium text-slate-700">
          Longitude <span class="text-slate-400 font-normal">(optional)</span>
        </label>
        <input
          type="number"
          step="any"
          :value="modelValue.lng ?? ''"
          @input="update('lng', ($event.target as HTMLInputElement).value || null)"
          placeholder="69.2401"
          class="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900"
        />
      </div>
    </div>

    <!-- Description -->
    <div class="space-y-1">
      <label class="block text-sm font-medium text-slate-700">
        Description <span class="text-slate-400 font-normal">(optional)</span>
      </label>
      <textarea
        :value="modelValue.description"
        @input="update('description', ($event.target as HTMLTextAreaElement).value)"
        placeholder="A welcoming barbershop in the heart of the city..."
        rows="3"
        class="w-full px-3 py-2 border border-slate-200 rounded-lg bg-white text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-900/20 focus:border-slate-900 resize-none"
      />
    </div>
  </div>
</template>
