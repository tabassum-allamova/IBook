import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'
import router from './router'
import { useAuthStore } from './stores/auth'
import { initAxiosStore } from './lib/axios'
import './assets/main.css'
import App from './App.vue'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)
app.use(VueQueryPlugin)

// Wire up axios store access after pinia is installed
initAxiosStore(() => useAuthStore())

app.mount('#app')
