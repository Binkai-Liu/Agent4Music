/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        music: {
          blue: '#1e6fff',
          purple: '#7c3aed',
        },
      },
    },
  },
  plugins: [],
}
