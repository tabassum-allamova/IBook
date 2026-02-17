<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation } from '@tanstack/vue-query'
import api from '@/lib/axios'
import ShopWizardStep1 from '@/components/shop/ShopWizardStep1.vue'
import ShopWizardStep2 from '@/components/shop/ShopWizardStep2.vue'
import ShopWizardStep3 from '@/components/shop/ShopWizardStep3.vue'

const router = useRouter()

const currentStep = ref(1)
const totalSteps = 3
const submitError = ref<string | null>(null)

const shopForm = reactive({
  name: '',
  address: '',
  lat: null as string | null,
  lng: null as string | null,
  description: '',
  hours: Array.from({ length: 7 }, (_, i) => ({
    day_of_week: i,
    is_open: i < 5,
    opens_at: '09:00',
    closes_at: '18:00',
    break_start: '13:00',
    break_end: '14:00',
  })),
  photos: [] as File[],
})

// Step 1 form data shape for v-model binding
const step1Data = reactive({
  name: shopForm.name,
  address: shopForm.address,
  lat: shopForm.lat,
  lng: shopForm.lng,
  description: shopForm.description,
})

// Keep shopForm in sync with step1Data
function onStep1Update(val: typeof step1Data) {
  shopForm.name = val.name
  shopForm.address = val.address
  shopForm.lat = val.lat
  shopForm.lng = val.lng
  shopForm.description = val.description
  Object.assign(step1Data, val)
}

// Step 2 shape for v-model
const step2Data = reactive({ hours: shopForm.hours })

function onStep2Update(val: { hours: typeof shopForm.hours }) {
  shopForm.hours = val.hours
  step2Data.hours = val.hours
}

function validateCurrentStep(): boolean {
  if (currentStep.value === 1) {
    return shopForm.name.trim().length > 0 && shopForm.address.trim().length > 0
  }
  return true
}

const step1Error = ref('')

function nextStep() {
  if (!validateCurrentStep()) {
    if (currentStep.value === 1) {
      step1Error.value = 'Shop name and address are required'
    }
    return
  }
  step1Error.value = ''
  if (currentStep.value < totalSteps) {
    currentStep.value++
  }
}

function prevStep() {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

// Mutations
const createShopMutation = useMutation({
  mutationFn: (payload: {
    name: string
    address: string
    lat: string | null
    lng: string | null
    description: string
  }) => api.post('/api/shops/', payload).then((r) => r.data),
})

const updateHoursMutation = useMutation({
  mutationFn: ({ shopId, hours }: { shopId: number; hours: typeof shopForm.hours }) =>
    api.put(`/api/shops/${shopId}/hours/`, hours),
})

const uploadPhotosMutation = useMutation({
  mutationFn: ({ shopId, files }: { shopId: number; files: File[] }) => {
    const form = new FormData()
    files.forEach((f) => form.append('image', f))
    return api.post(`/api/shops/${shopId}/photos/`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
})

const isSubmitting = ref(false)

async function handleSubmit() {
  if (!validateCurrentStep()) return

  isSubmitting.value = true
  submitError.value = null

  try {
    // Step 1: Create shop
    const shop = await createShopMutation.mutateAsync({
      name: shopForm.name,
      address: shopForm.address,
      lat: shopForm.lat,
      lng: shopForm.lng,
      description: shopForm.description,
    })

    const shopId = shop.id

    // Step 2: Update hours (PUT bulk-upsert)
    await updateHoursMutation.mutateAsync({ shopId, hours: shopForm.hours })

    // Step 3: Upload photos if any
    if (shopForm.photos.length > 0) {
      await uploadPhotosMutation.mutateAsync({ shopId, files: shopForm.photos })
    }

    // Success — redirect to shop management page
    router.push('/owner/shop')
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    submitError.value =
      axiosErr?.response?.data?.detail ?? 'Failed to create shop. Please try again.'
  } finally {
    isSubmitting.value = false
  }
}

</script>

<template>
  <div class="min-h-screen bg-ibook-cream flex items-center justify-center p-4">
    <div class="w-full max-w-2xl">
      <!-- Header -->
      <div class="mb-8 text-center">
        <h1 class="text-3xl font-bold text-ibook-brown-700">Create Your Shop</h1>
        <p class="text-ibook-brown-400 mt-2">Step {{ currentStep }} of {{ totalSteps }}</p>
      </div>

      <!-- Progress bar -->
      <div class="mb-8">
        <div class="h-2 bg-ibook-brown-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-ibook-gold-500 rounded-full transition-all duration-300"
            :style="{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }"
          />
        </div>
        <div class="flex justify-between mt-2">
          <span
            v-for="step in totalSteps"
            :key="step"
            class="text-xs font-medium"
            :class="step <= currentStep ? 'text-ibook-gold-600' : 'text-ibook-brown-400'"
          >
            Step {{ step }}
          </span>
        </div>
      </div>

      <!-- Step Content Card -->
      <div class="bg-white rounded-2xl shadow-sm border border-ibook-brown-100 p-8">
        <!-- Step 1 -->
        <ShopWizardStep1
          v-if="currentStep === 1"
          :model-value="step1Data"
          @update:model-value="onStep1Update"
        />

        <!-- Step 2 -->
        <ShopWizardStep2
          v-else-if="currentStep === 2"
          :model-value="step2Data"
          @update:model-value="onStep2Update"
        />

        <!-- Step 3 -->
        <ShopWizardStep3
          v-else-if="currentStep === 3"
          :model-value="shopForm.photos"
          @update:model-value="(files) => (shopForm.photos = files)"
        />

        <!-- Validation error -->
        <p v-if="step1Error && currentStep === 1" class="mt-3 text-sm text-red-500">
          {{ step1Error }}
        </p>

        <!-- Submit error -->
        <p v-if="submitError" class="mt-3 text-sm text-red-500">{{ submitError }}</p>

        <!-- Navigation buttons -->
        <div class="flex justify-between mt-8">
          <button
            v-if="currentStep > 1"
            type="button"
            @click="prevStep"
            class="px-5 py-2 rounded-lg border border-ibook-brown-200 text-ibook-brown-700 hover:bg-ibook-brown-50 font-medium transition-colors"
          >
            Back
          </button>
          <div v-else />

          <button
            v-if="currentStep < totalSteps"
            type="button"
            @click="nextStep"
            class="px-5 py-2 rounded-lg bg-ibook-gold-500 hover:bg-ibook-gold-600 text-white font-medium transition-colors"
          >
            Next
          </button>

          <button
            v-else
            type="button"
            @click="handleSubmit"
            :disabled="isSubmitting"
            class="px-5 py-2 rounded-lg bg-ibook-gold-500 hover:bg-ibook-gold-600 text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isSubmitting ? 'Creating...' : 'Create Shop' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
