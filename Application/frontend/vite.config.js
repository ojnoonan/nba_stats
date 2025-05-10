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
    host: '0.0.0.0',
    proxy: {
      '^/api/.*': {
        target: 'http://0.0.0.0:7778',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ''),
        secure: false,
        ws: true,
        headers: {
          'Origin': 'http://localhost:7779'
        }
      }
    }
  }
})
