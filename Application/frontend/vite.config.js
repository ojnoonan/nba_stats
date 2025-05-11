import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    target: 'es2015'
  },
  server: {
    host: true,
    port: 7779
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(mode)
  }
}))
