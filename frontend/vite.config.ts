import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],

  // CRITICAL: Use relative paths for PyWebView compatibility
  // PyWebView loads files from file:// protocol, not http://
  base: './',

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },

  build: {
    outDir: 'dist',
    // Generate source maps for debugging
    sourcemap: true,
    // Ensure assets use relative paths
    assetsDir: 'assets',
  },

  server: {
    // Development server port (Vite default)
    port: 5173,
    // Allow connections from PyWebView in debug mode
    host: true,
  },
})
