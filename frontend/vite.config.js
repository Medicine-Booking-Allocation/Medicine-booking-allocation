import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite dev server configuration.
//
// The browser talks same-origin to Vite (port 5173). Vite proxies every
// /api/* and /health request to the Flask backend (port 5000). Because the
// browser only ever talks to Vite, Flask session cookies flow transparently
// and no CORS configuration on the backend is required.
//
// To run the backend alongside this dev server:
//   1) Flask:  python run.py            (from repo root -> http://127.0.0.1:5000)
//   2) Vite:   npm run dev              (from frontend/ -> http://localhost:5173)
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
      '/health': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      },
    },
  },
})
