/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          bg: '#000000',
          panel: '#111111',
          border: '#333333',
        },
        accent: {
          cyan: '#00e5ff',
          hover: '#00b3cc',
        },
        status: {
          live: '#00e676',
          warning: '#ffab00',
          critical: '#ff1744',
          uncertain: '#ffeb3b',
          fault: '#9e9e9e',
        },
        // Legacy aliases for old component compat
        dashboard: {
          bg: '#000000',
          card: '#111111',
          border: '#333333',
          textMain: '#e5e7eb',
          textMuted: '#6b7280',
        },
        critical: '#ff1744',
        warning: '#ffab00',
        normal: '#00e676',
      },
      fontFamily: {
        mono: ['"Share Tech Mono"', 'monospace'],
        sans: ['"Rajdhani"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
