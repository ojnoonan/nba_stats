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
  server: {
    port: 7779,
    proxy: {
      '^/(games|teams|players|search)': {
        target: 'http://localhost:7778',
        changeOrigin: true
      }
    }
  },
  preview: {
    port: 7779
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom', 'react-router-dom']
        }
      }
    }
  }
})
