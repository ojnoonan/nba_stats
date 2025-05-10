import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '/src': path.resolve(__dirname, 'src')
    }
  },
  css: {
    postcss: './postcss.config.cjs'
  },
  preview: {
    port: 7779,
    proxy: {
      '/api': {
        target: 'http://localhost:7778',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        secure: false
      }
    }
  }
})
