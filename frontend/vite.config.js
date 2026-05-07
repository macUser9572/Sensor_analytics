import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load ALL env vars (empty prefix) so ${M2_IP} etc. are expanded correctly.
  const env = loadEnv(mode, process.cwd(), '')
  const apiBase =
    env.VITE_BACKEND_URL ||
    env.VITE_API_URL ||
    env.REACT_API_BASE_URL ||
    'http://localhost:8000'

  return {
    plugins: [react()],
    envPrefix: ['VITE_', 'REACT_'],
    server: {
      port: 3000,
      host: '0.0.0.0',
      // In development the React app is served from localhost:3000 while the
      // backend lives on a different host. Proxying HTTP backend paths through
      // Vite eliminates cross-origin browser requests.
      proxy: {
        '/data':   { target: apiBase, changeOrigin: true },
        '/api':    { target: apiBase, changeOrigin: true },
        '/health': { target: apiBase, changeOrigin: true },
        '/simulator': { target: apiBase, changeOrigin: true },
      },
    },
  }
})
