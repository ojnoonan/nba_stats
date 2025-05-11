import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom'],
          ui: ['@headlessui/react', '@radix-ui/react-dialog', '@radix-ui/react-tooltip'],
          data: ['@tanstack/react-query', '@tanstack/react-table']
        }
      }
    }
  },
  server: {
    host: true,
    port: 7779
  }
})
