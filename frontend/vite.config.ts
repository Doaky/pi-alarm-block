import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true // Allow connections from network
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true
  }
})
