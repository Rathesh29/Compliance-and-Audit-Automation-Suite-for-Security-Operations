/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        navy: {
          900: '#0b132b',
          800: '#1c2541',
          700: '#3a506b',
        },
        slate: {
          850: '#172033',
        },
        brand: {
          primary: '#1e40af',
          secondary: '#0284c7',
          accent: '#0d9488',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          critical: '#dc2626'
        }
      }
    },
  },
  plugins: [],
}
