/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Terminal background layers
        terminal: {
          bg:      '#0D0F14',
          surface: '#13161E',
          panel:   '#1A1D27',
          border:  '#252836',
          muted:   '#2E3245',
        },
        // Data colours
        up:       '#22C55E',
        down:     '#EF4444',
        neutral:  '#94A3B8',
        accent:   '#3B82F6',
        warning:  '#F59E0B',
        // ATM highlight
        atm:      '#1E3A5F',
        'atm-border': '#3B82F6',
        // Greeks
        delta:    '#60A5FA',
        gamma:    '#34D399',
        vega:     '#A78BFA',
        theta:    '#F87171',
        rho:      '#FBBF24',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
        sans: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        'xxs': '0.65rem',
        'xs':  '0.75rem',
        'sm':  '0.8125rem',
      },
      borderWidth: {
        DEFAULT: '1px',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in':    'fadeIn 0.2s ease-in-out',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0', transform: 'translateY(-4px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
