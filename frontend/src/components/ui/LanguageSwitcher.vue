<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { LOCALES, setLocale, type LocaleCode } from '@/i18n'

const { locale, t } = useI18n()
const open = ref(false)
const rootRef = ref<HTMLElement | null>(null)

const current = computed(
  () => LOCALES.find((l) => l.code === locale.value) ?? LOCALES[0],
)

function toggle() {
  open.value = !open.value
}
function choose(code: LocaleCode) {
  setLocale(code)
  open.value = false
}
function onDocumentClick(e: MouseEvent) {
  if (!rootRef.value) return
  if (!rootRef.value.contains(e.target as Node)) open.value = false
}
function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape' && open.value) open.value = false
}

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  document.addEventListener('keydown', onKeydown)
})
onUnmounted(() => {
  document.removeEventListener('click', onDocumentClick)
  document.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div ref="rootRef" class="relative">
    <button
      type="button"
      :aria-label="t('common.language')"
      :aria-expanded="open"
      aria-haspopup="listbox"
      class="inline-flex items-center gap-1.5 h-9 px-3 rounded-md border border-slate-200 bg-white text-sm font-medium text-slate-700 hover:text-slate-900 hover:border-slate-400 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/70"
      @click="toggle"
    >
      <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="12" cy="12" r="9" />
        <path stroke-linecap="round" stroke-linejoin="round" d="M3 12h18M12 3c2.5 2.7 4 6.1 4 9s-1.5 6.3-4 9c-2.5-2.7-4-6.1-4-9s1.5-6.3 4-9z" />
      </svg>
      <span class="uppercase tracking-wide">{{ current.code }}</span>
      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" aria-hidden="true">
        <path stroke-linecap="round" stroke-linejoin="round" d="M19 9l-7 7-7-7" />
      </svg>
    </button>

    <Transition
      enter-active-class="transition duration-150 ease-out"
      enter-from-class="opacity-0 -translate-y-1"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition duration-100 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <ul
        v-if="open"
        role="listbox"
        :aria-label="t('common.language')"
        class="absolute right-0 mt-2 w-44 bg-white rounded-md border border-slate-200 shadow-lg py-1 z-50"
      >
        <li v-for="option in LOCALES" :key="option.code">
          <button
            type="button"
            role="option"
            :aria-selected="option.code === locale"
            class="w-full text-left px-3 py-2 text-sm flex items-center justify-between transition-colors focus:outline-none"
            :class="
              option.code === locale
                ? 'bg-slate-50 text-slate-900 font-medium'
                : 'text-slate-700 hover:bg-slate-50 hover:text-slate-900'
            "
            @click="choose(option.code)"
          >
            <span>{{ option.nativeLabel }}</span>
            <span
              v-if="option.code === locale"
              class="text-slate-900"
              aria-hidden="true"
            >
              <svg class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2.4" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </span>
          </button>
        </li>
      </ul>
    </Transition>
  </div>
</template>
