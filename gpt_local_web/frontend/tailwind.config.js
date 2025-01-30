/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dark: {
          DEFAULT: '#2a2a2a',
          darker: '#0a0a0a',
          lighter: '#2a2a2a'
        }
      }
    },
  },
  plugins: [],
}
