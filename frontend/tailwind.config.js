/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'chat-bg': '#181A20',
        'chat-sidebar': '#23272F',
        'chat-input': '#23272F',
        'chat-border': '#353945',
        'chat-user': '#2563eb',
        'chat-assistant': '#23272F',
        'chat-user-bubble': '#2D313A',
        'chat-accent': '#4F8CFF',
        'chat-accent-green': '#22D3A8',
        'chat-accent-pink': '#F472B6',
        'chat-accent-yellow': '#FBBF24',
        'chat-glass': 'rgba(35,39,47,0.8)',
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
  ],
} 