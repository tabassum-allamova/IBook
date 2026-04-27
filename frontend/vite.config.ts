import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    host: '0.0.0.0',
    proxy: {
      // changeOrigin stays false so Django sees the browser's Host header,
      // and build_absolute_uri() produces URLs the browser can actually fetch.
      // /media must be proxied so image URLs returned by the API resolve here.
      '/api': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8001',
        changeOrigin: false,
      },
      '/media': {
        target: process.env.VITE_BACKEND_URL || 'http://localhost:8001',
        changeOrigin: false,
      },
    },
  },
})
