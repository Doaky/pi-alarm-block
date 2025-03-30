import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig(({ mode }) => ({
  plugins: [react()],
  server: {
    // In development, proxy API requests to local backend
    proxy: mode === 'development' ? {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    } : undefined,
    // Allow connections from local network in development
    host: '0.0.0.0'
  },
  build: {
    outDir: 'dist',
    assetsDir: 'assets',
    emptyOutDir: true,
    // Generate sourcemaps for easier debugging
    sourcemap: true
  },
  // Ensure environment variables are loaded
  envDir: '.'
}))
