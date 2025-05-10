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
  define: {
    'process.env.VITE_API_URL': JSON.stringify('http://localhost:7778')
  }
})
