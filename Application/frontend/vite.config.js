import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  base: '/',
  server: {
    port: 7779,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:7778',
        changeOrigin: true,
        secure: false,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    minify: false, // Disable minification temporarily for debugging
    sourcemap: true,
    outDir: 'dist',
    emptyOutDir: true,
    reportCompressedSize: false // Disable size reporting for faster builds
  }
})
