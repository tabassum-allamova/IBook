<script setup lang="ts">
import { nextTick, onMounted, onUnmounted, ref, watch } from 'vue'

const props = withDefaults(
  defineProps<{
    open: boolean
    title?: string
    eyebrow?: string
    size?: 'sm' | 'md' | 'lg' | 'xl'
    closeOnBackdrop?: boolean
    hideHeader?: boolean
  }>(),
  {
    size: 'md',
    closeOnBackdrop: true,
    hideHeader: false,
  },
)

const emit = defineEmits<{ close: [] }>()

const sizeClass: Record<NonNullable<typeof props.size>, string> = {
  sm: 'md:max-w-sm',
  md: 'md:max-w-lg',
  lg: 'md:max-w-2xl',
  xl: 'md:max-w-3xl',
}

const panelRef = ref<HTMLElement | null>(null)
let lastFocused: HTMLElement | null = null

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'

function focusablesInPanel(): HTMLElement[] {
  if (!panelRef.value) return []
  return Array.from(panelRef.value.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(
    (el) => !el.hasAttribute('inert') && el.offsetParent !== null,
  )
}

function close() {
  emit('close')
}
function onBackdropClick() {
  if (props.closeOnBackdrop) close()
}
function onKeydown(e: KeyboardEvent) {
  if (!props.open) return
  if (e.key === 'Escape') {
    close()
    return
  }
  if (e.key !== 'Tab') return
  const focusables = focusablesInPanel()
  if (focusables.length === 0) {
    e.preventDefault()
    return
  }
  const first = focusables[0]
  const last = focusables[focusables.length - 1]
  const active = document.activeElement as HTMLElement | null
  if (e.shiftKey && (active === first || !panelRef.value?.contains(active))) {
    e.preventDefault()
    last.focus()
  } else if (!e.shiftKey && active === last) {
    e.preventDefault()
    first.focus()
  }
}

watch(
  () => props.open,
  async (v) => {
    if (typeof document === 'undefined') return
    document.body.style.overflow = v ? 'hidden' : ''
    if (v) {
      lastFocused = document.activeElement as HTMLElement | null
      await nextTick()
      const focusables = focusablesInPanel()
      // Prefer the first content-focusable over the close button so keyboard
      // users land on something useful (usually a form field or primary CTA).
      const firstInteractive =
        focusables.find((el) => el.getAttribute('aria-label') !== 'Close') ?? focusables[0]
      firstInteractive?.focus()
    } else if (lastFocused && typeof lastFocused.focus === 'function') {
      lastFocused.focus()
      lastFocused = null
    }
  },
  { immediate: true },
)

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
  if (typeof document !== 'undefined') document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="open"
        class="modal-overlay fixed inset-0 z-50 bg-slate-900/40 flex items-end md:items-center justify-center md:p-4"
        role="dialog"
        aria-modal="true"
        :aria-label="title || undefined"
        @click.self="onBackdropClick"
      >
        <div
          ref="panelRef"
          class="modal-panel w-full bg-white rounded-t-2xl md:rounded-2xl shadow-2xl max-h-[92vh] overflow-y-auto flex flex-col"
          :class="sizeClass[size]"
          tabindex="-1"
          @click.stop
        >
          <div
            v-if="!hideHeader && ($slots.header || title || eyebrow)"
            class="flex items-start justify-between gap-4 px-5 md:px-6 py-4 border-b border-slate-200"
          >
            <div class="min-w-0 flex-1">
              <slot name="header">
                <p v-if="eyebrow" class="text-sm font-medium text-slate-500 capitalize truncate">
                  {{ eyebrow }}
                </p>
                <h2
                  class="text-xl font-semibold text-slate-900 tracking-tight"
                  :class="eyebrow ? 'mt-0.5' : ''"
                >
                  {{ title }}
                </h2>
              </slot>
            </div>
            <button
              type="button"
              aria-label="Close"
              class="flex-shrink-0 h-9 w-9 inline-flex items-center justify-center rounded-md text-slate-500 hover:text-slate-900 hover:bg-slate-100 transition-colors"
              @click="close"
            >
              <svg class="h-5 w-5" fill="none" stroke="currentColor" stroke-width="1.8" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <div class="flex-1 min-h-0">
            <slot />
          </div>

          <div
            v-if="$slots.footer"
            class="px-5 md:px-6 py-4 border-t border-slate-200"
          >
            <slot name="footer" />
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-enter-active,
.modal-leave-active {
  transition: opacity 180ms ease-out;
}
.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .modal-panel,
.modal-leave-active .modal-panel {
  transition:
    transform 240ms cubic-bezier(0.2, 0.9, 0.2, 1),
    opacity 200ms ease-out;
}
.modal-enter-from .modal-panel,
.modal-leave-to .modal-panel {
  opacity: 0;
  transform: translateY(24px);
}

@media (min-width: 768px) {
  .modal-enter-from .modal-panel,
  .modal-leave-to .modal-panel {
    transform: translateY(8px) scale(0.96);
  }
}

@media (prefers-reduced-motion: reduce) {
  .modal-enter-active,
  .modal-leave-active,
  .modal-enter-active .modal-panel,
  .modal-leave-active .modal-panel {
    transition-duration: 0ms;
  }
  .modal-enter-from .modal-panel,
  .modal-leave-to .modal-panel {
    transform: none;
  }
}
</style>
