import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Emberholm amber palette
        ember: {
          50: '#fff8ed',
          100: '#ffeed4',
          200: '#ffd9a8',
          300: '#ffbd71',
          400: '#ff9500', // Primary amber
          500: '#f97316',
          600: '#ea5a0c',
          700: '#c2400c',
          800: '#9a3412',
          900: '#7c2d12',
          950: '#431407',
        },
        // Dark backgrounds
        void: {
          DEFAULT: '#0a0705',
          light: '#1a1410',
          lighter: '#2a221a',
        },
        // Accent colors
        spark: '#ffd700',
        ash: '#4a4a4a',
        flame: '#ff4500',
      },
      fontFamily: {
        pixel: ['Pixelify Sans', 'monospace'],
        alagard: ['Alagard', 'serif'],
        mono: ['Courier New', 'monospace'],
      },
      animation: {
        'glow': 'glow 2s ease-in-out infinite alternate',
        'flicker': 'flicker 0.15s infinite',
        'scanline': 'scanline 8s linear infinite',
        'typewriter': 'typewriter 2s steps(40) forwards',
        'blink': 'blink 1s step-end infinite',
        'fade-in': 'fadeIn 0.5s ease-out forwards',
        'slide-up': 'slideUp 0.3s ease-out forwards',
      },
      keyframes: {
        glow: {
          '0%': { textShadow: '0 0 5px #ff9500, 0 0 10px #ff9500' },
          '100%': { textShadow: '0 0 10px #ff9500, 0 0 20px #ff9500, 0 0 30px #ff9500' },
        },
        flicker: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.8' },
        },
        scanline: {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(100vh)' },
        },
        typewriter: {
          'from': { width: '0' },
          'to': { width: '100%' },
        },
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        fadeIn: {
          'from': { opacity: '0' },
          'to': { opacity: '1' },
        },
        slideUp: {
          'from': { opacity: '0', transform: 'translateY(10px)' },
          'to': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'ember': '0 0 10px rgba(255, 149, 0, 0.5)',
        'ember-lg': '0 0 20px rgba(255, 149, 0, 0.7)',
        'inner-ember': 'inset 0 0 20px rgba(255, 149, 0, 0.3)',
      },
    },
  },
  plugins: [],
};

export default config;
