/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ivory: {
          50: '#FDFCF9',
          100: '#FAF8F5',
          200: '#F4EFEB',
          300: '#ECE4DC',
          400: '#DDD2C5',
          500: '#C8BAAA',
        },
        forest: {
          50: '#F0F5F2',
          100: '#E1EBE5',
          200: '#C3D8CC',
          300: '#95BDA7',
          400: '#629B7E',
          500: '#3D7D5E',
          600: '#2E634A',
          700: '#26503D',
          800: '#204032',
          900: '#1A3429',
          950: '#0F2119',
        },
        charcoal: {
          50: '#F6F6F6',
          100: '#E7E7E7',
          200: '#D1D1D1',
          300: '#B0B0B0',
          400: '#888888',
          500: '#6D6D6D',
          600: '#5D5D5D',
          700: '#4F4F4F',
          800: '#333333',
          900: '#1F2421',
          950: '#141716',
        },
        risk: {
          low: '#1E5E43',
          lowBg: '#EAF5EF',
          lowBorder: '#BFE3CE',
          mod: '#B45309',
          modBg: '#FEF3C7',
          modBorder: '#FDE68A',
          high: '#B91C1C',
          highBg: '#FEE2E2',
          highBorder: '#FECACA',
        }
      },
      fontFamily: {
        serif: ['Newsreader', 'Georgia', 'Cambria', 'serif'],
        sans: ['Plus Jakarta Sans', 'Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'subtle': '0 1px 3px 0 rgba(31, 36, 33, 0.04), 0 1px 2px -1px rgba(31, 36, 33, 0.04)',
        'card': '0 4px 12px -2px rgba(31, 36, 33, 0.05), 0 2px 6px -2px rgba(31, 36, 33, 0.03)',
        'elevated': '0 12px 24px -4px rgba(31, 36, 33, 0.08), 0 4px 10px -3px rgba(31, 36, 33, 0.04)',
      }
    },
  },
  plugins: [],
}

