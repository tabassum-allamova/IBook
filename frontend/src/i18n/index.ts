import { createI18n } from 'vue-i18n'
import en from './locales/en.json'
import ru from './locales/ru.json'
import uz from './locales/uz.json'

export type LocaleCode = 'en' | 'ru' | 'uz'

export interface LocaleOption {
  code: LocaleCode
  label: string
  nativeLabel: string
}

export const LOCALES: LocaleOption[] = [
  { code: 'en', label: 'English', nativeLabel: 'English' },
  { code: 'ru', label: 'Russian', nativeLabel: 'Русский' },
  { code: 'uz', label: 'Uzbek', nativeLabel: 'O‘zbekcha' },
]

const STORAGE_KEY = 'ibook_locale'
const DEFAULT_LOCALE: LocaleCode = 'en'

function resolveInitial(): LocaleCode {
  if (typeof localStorage !== 'undefined') {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved && LOCALES.some((l) => l.code === saved)) {
      return saved as LocaleCode
    }
  }
  if (typeof navigator !== 'undefined') {
    const navLang = (navigator.language || '').slice(0, 2).toLowerCase()
    if (LOCALES.some((l) => l.code === navLang)) return navLang as LocaleCode
  }
  return DEFAULT_LOCALE
}

export const i18n = createI18n({
  legacy: false,
  globalInjection: true,
  locale: resolveInitial(),
  fallbackLocale: DEFAULT_LOCALE,
  messages: { en, ru, uz },
})

export function setLocale(code: LocaleCode) {
  if (!LOCALES.some((l) => l.code === code)) return
  i18n.global.locale.value = code
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem(STORAGE_KEY, code)
  }
  if (typeof document !== 'undefined') {
    document.documentElement.lang = code
  }
}

export function currentLocale(): LocaleCode {
  return i18n.global.locale.value as LocaleCode
}
