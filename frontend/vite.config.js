import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Fixed file names (no content hash), so benchmark URLs stay the same across
// builds: /assets/index.js, /assets/vendor.js, /assets/index.css, /assets/hero.webp
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        entryFileNames: 'assets/[name].js',
        chunkFileNames: 'assets/[name].js',
        assetFileNames: 'assets/[name][extname]',
        // React and other deps in their own chunk, like a typical SPA build
        manualChunks: (id) => (id.includes('node_modules') ? 'vendor' : undefined),
      },
    },
  },
})
