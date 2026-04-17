/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        normal: '#22c55e',
        warning: '#f59e0b',
        critical: '#ef4444',
        dashboard: {
          bg: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          textMain: '#f1f5f9',
          textMuted: '#94a3b8'
        }
      }
    },
  },
  plugins: [],
}
