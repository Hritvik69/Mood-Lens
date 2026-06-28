/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class', // Enables class-based dark mode
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f3ff',
          100: '#edd8ff',
          200: '#d9b3ff',
          300: '#bd80ff',
          400: '#9e4dff',
          500: '#7e1aff',
          600: '#6600e6',
          700: '#5200b3',
          800: '#3e0080',
          900: '#2b0059',
          accent: '#00f2fe',
        },
        slate: {
          950: '#030712',
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'sans-serif'],
      },
      backdropBlur: {
        xs: '2px',
      }
    },
  },
  plugins: [],
}
