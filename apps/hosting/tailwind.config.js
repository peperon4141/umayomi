import { defineConfig } from 'tailwindcss'
import tailwindcssPrimeui from 'tailwindcss-primeui'

export default defineConfig({
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  plugins: [tailwindcssPrimeui],
})
