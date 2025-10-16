import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(),tailwindcss()],
  optimizeDeps: {
    include: ["three", "postprocessing"],
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    watch:{
      usePolling:true
    },
    proxy: {
      '^/(app|api|assets|files)': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: false,
        secure: true,
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  build: {
    outDir: '../pix_one/public/dashboard',
    emptyOutDir: true,
    target: 'es2015',
  },
})