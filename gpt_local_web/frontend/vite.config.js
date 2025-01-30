import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue()],
  server: {
    allowedHosts: ['ogolfen.ddns.net'],
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/api-ssl': {
        target: 'https://ogolfen,ddns.net:3545',
        changeOrigin: true,
        secure: true, // Usa true si el certificado es válido
        //rewrite: (path) => path.replace(/^\/api-ssl/, ''),
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
      '/ws-ssl': {
        target: 'wss://ogolfen,ddns.net:3545',
        ws: true,
        secure: true, // Si tu certificado es auto-firmado, dejar en false
      },
    }
  }
})
