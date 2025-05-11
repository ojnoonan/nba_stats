import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 7779
  },
  preview: {
    port: 7779
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets'
  }
})
