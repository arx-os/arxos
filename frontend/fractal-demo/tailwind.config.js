/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'arxos-blue': '#0066cc',
        'arxos-dark': '#1a1a1a',
        'arxos-gray': '#333333',
        'arxos-light': '#f5f5f5',
      },
      animation: {
        'zoom-in': 'zoomIn 0.3s ease-out',
        'zoom-out': 'zoomOut 0.3s ease-out',
        'pan': 'pan 0.5s ease-out',
        'fade-in': 'fadeIn 0.2s ease-out',
      },
      keyframes: {
        zoomIn: {
          '0%': { transform: 'scale(1)', opacity: '0.8' },
          '100%': { transform: 'scale(1.1)', opacity: '1' },
        },
        zoomOut: {
          '0%': { transform: 'scale(1)', opacity: '0.8' },
          '100%': { transform: 'scale(0.9)', opacity: '1' },
        },
        pan: {
          '0%': { transform: 'translateX(0) translateY(0)' },
          '100%': { transform: 'translateX(var(--pan-x)) translateY(var(--pan-y))' },
        },
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}