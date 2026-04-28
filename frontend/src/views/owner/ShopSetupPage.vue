<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useMutation } from '@tanstack/vue-query'
import { useToast } from 'vue-toastification'
import OwnerLayout from '@/layouts/OwnerLayout.vue'
import api from '@/lib/axios'
import ShopWizardStep1 from '@/components/shop/ShopWizardStep1.vue'
import ShopWizardStep2 from '@/components/shop/ShopWizardStep2.vue'
import ShopWizardStep3 from '@/components/shop/ShopWizardStep3.vue'

const toast = useToast()

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

    // Success — shop management page was removed; send the owner to their
    // dashboard instead.
    toast.success('Shop created successfully!')
    router.push('/owner/overview')
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { detail?: string } } }
    submitError.value =
      axiosErr?.response?.data?.detail ?? 'Failed to create shop. Please try again.'
    toast.error(submitError.value)
  } finally {
    isSubmitting.value = false
  }
}

</script>

<template>
  <OwnerLayout>
    <section class="max-w-3xl mx-auto">
      <!-- Header -->
      <div class="mb-8">
        <h1 class="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight leading-tight">
          Create your shop
        </h1>
        <p class="mt-1 text-sm text-slate-600">Step {{ currentStep }} of {{ totalSteps }}</p>
      </div>

      <!-- Progress bar -->
      <div class="mb-8">
        <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            class="h-full bg-slate-900 rounded-full transition-all duration-300"
            :style="{ width: `${((currentStep - 1) / (totalSteps - 1)) * 100}%` }"
          />
        </div>
        <div class="flex justify-between mt-2">
          <span
            v-for="step in totalSteps"
            :key="step"
            class="text-sm font-medium"
            :class="step <= currentStep ? 'text-slate-900' : 'text-slate-400'"
          >
            Step {{ step }}
          </span>
        </div>
      </div>

      <!-- Step Content Card -->
      <div class="bg-white rounded-xl border border-slate-200 p-6 md:p-8">
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
            class="inline-flex items-center justify-center gap-1.5 h-10 px-4 rounded-lg border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors"
            @click="prevStep"
          >
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
            </svg>
            Back
          </button>
          <div v-else />

          <button
            v-if="currentStep < totalSteps"
            type="button"
            class="inline-flex items-center justify-center gap-1.5 h-10 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors"
            @click="nextStep"
          >
            Next
            <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
            </svg>
          </button>

          <button
            v-else
            type="button"
            class="inline-flex items-center justify-center gap-2 h-10 px-5 rounded-lg bg-slate-900 hover:bg-slate-800 text-white text-sm font-semibold transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
            :disabled="isSubmitting"
            @click="handleSubmit"
          >
            <svg v-if="isSubmitting" class="h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-30" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="3" />
              <path class="opacity-90" fill="currentColor" d="M4 12a8 8 0 018-8v3a5 5 0 00-5 5H4z" />
            </svg>
            {{ isSubmitting ? 'Creating…' : 'Create shop' }}
          </button>
        </div>
      </div>
    </section>
  </OwnerLayout>
</template>
