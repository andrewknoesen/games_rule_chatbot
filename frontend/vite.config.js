import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    proxy: {
      '/api': {
        // API_TARGET=http://192.168.0.200:8720 to develop against the homelab API.
        target: process.env.API_TARGET || 'http://localhost:8000',
        rewrite: path => path.replace(/^\/api/, '')
      }
    }
  }
})
