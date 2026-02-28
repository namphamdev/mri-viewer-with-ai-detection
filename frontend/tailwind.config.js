/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        medical: {
          bg: '#0a0e17',
          surface: '#111827',
          panel: '#1a2332',
          border: '#2a3a4e',
          accent: '#3b82f6',
          'accent-hover': '#2563eb',
          text: '#e2e8f0',
          'text-muted': '#94a3b8',
          success: '#22c55e',
          warning: '#f59e0b',
          error: '#ef4444',
        },
      },
    },
  },
  plugins: [],
};
