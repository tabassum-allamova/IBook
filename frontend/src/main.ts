import { createApp } from 'vue'
import { createPinia } from 'pinia'
import { VueQueryPlugin } from '@tanstack/vue-query'
import Toast from 'vue-toastification'
import 'vue-toastification/dist/index.css'
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
app.use(Toast, {
  position: 'bottom-center',
  timeout: 3000,
  closeOnClick: true,
  pauseOnHover: true,
  draggable: false,
  hideProgressBar: true,
})

initAxiosStore(() => useAuthStore())

app.mount('#app')
