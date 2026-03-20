/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        sds: {
          bg:            '#07021A',
          darker:        '#0D0520',
          dark:          '#120828',
          card:          '#1A0F3C',
          'card-light':  '#211445',
          border:        '#2E1A6A',
          'border-bright':'#4A2D9E',
          purple:        '#5B35C4',
          'purple-bright':'#7B55E0',
          'purple-glow': '#9B75FF',
          orange:        '#FF6630',
          'orange-light':'#FF8C58',
          'orange-glow': '#FF6630',
          muted:         '#8B7DB8',
          'muted-light': '#B0A4D4',
          white:         '#F0EBF8',
        },
      },
      animation: {
        'fade-in':      'fadeIn 0.6s ease-out forwards',
        'fade-in-up':   'fadeInUp 0.5s ease-out forwards',
        'fade-in-up-d1':'fadeInUp 0.5s 0.1s ease-out forwards',
        'fade-in-up-d2':'fadeInUp 0.5s 0.2s ease-out forwards',
        'fade-in-up-d3':'fadeInUp 0.5s 0.3s ease-out forwards',
        'fade-in-up-d4':'fadeInUp 0.5s 0.4s ease-out forwards',
        'float-1':      'float1 7s ease-in-out infinite',
        'float-2':      'float2 9s ease-in-out infinite',
        'float-3':      'float3 11s ease-in-out infinite',
        'orb-pulse':    'orbPulse 5s ease-in-out infinite alternate',
        'orb-pulse-2':  'orbPulse2 7s ease-in-out infinite alternate',
        'scan-line':    'scanLine 7s ease-in-out infinite',
        'particle-ping':'particlePing 2.5s ease-out infinite',
        'glow-pulse':   'glowPulse 2s ease-in-out infinite alternate',
        'border-glow':  'borderGlow 2s ease-in-out infinite alternate',
        'spin-slow':    'spin 25s linear infinite',
        'marquee':      'marquee 20s linear infinite',
        'slide-in':     'slideIn 0.35s ease-out',
        'count-bar':    'countBar 1.2s cubic-bezier(0.4,0,0.2,1) forwards',
      },
      keyframes: {
        fadeIn: {
          '0%':   { opacity: '0' },
          '100%': { opacity: '1' },
        },
        fadeInUp: {
          '0%':   { opacity: '0', transform: 'translateY(22px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        float1: {
          '0%,100%': { transform: 'translate(0,0) rotate(0deg)' },
          '33%':     { transform: 'translate(12px,-18px) rotate(3deg)' },
          '66%':     { transform: 'translate(-8px,-8px) rotate(-2deg)' },
        },
        float2: {
          '0%,100%': { transform: 'translate(0,0) rotate(0deg)' },
          '40%':     { transform: 'translate(-14px,-20px) rotate(-4deg)' },
          '70%':     { transform: 'translate(8px,-10px) rotate(3deg)' },
        },
        float3: {
          '0%,100%': { transform: 'translate(0,0)' },
          '50%':     { transform: 'translate(10px,-15px)' },
        },
        orbPulse: {
          '0%':   { transform: 'scale(1)',    opacity: '0.25' },
          '100%': { transform: 'scale(1.35)', opacity: '0.45' },
        },
        orbPulse2: {
          '0%':   { transform: 'scale(1.1)', opacity: '0.18' },
          '100%': { transform: 'scale(0.8)', opacity: '0.35' },
        },
        particlePing: {
          '0%':   { transform: 'scale(1)',   opacity: '0.7' },
          '70%':  { transform: 'scale(2.5)', opacity: '0' },
          '100%': { transform: 'scale(2.5)', opacity: '0' },
        },
        scanLine: {
          '0%':   { transform: 'translateY(-100%)', opacity: '0' },
          '20%':  { opacity: '1' },
          '80%':  { opacity: '1' },
          '100%': { transform: 'translateY(400%)', opacity: '0' },
        },
        glowPulse: {
          '0%':   { textShadow: '0 0 8px rgba(255,102,48,0.4)' },
          '100%': { textShadow: '0 0 20px rgba(255,102,48,0.9), 0 0 40px rgba(255,102,48,0.4)' },
        },
        borderGlow: {
          '0%':   { boxShadow: '0 0 0px rgba(255,102,48,0)' },
          '100%': { boxShadow: '0 0 12px rgba(255,102,48,0.5), inset 0 0 8px rgba(255,102,48,0.1)' },
        },
        slideIn: {
          '0%':   { opacity: '0', transform: 'translateX(-12px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
        countBar: {
          '0%':   { width: '0%' },
          '100%': { width: 'var(--bar-w)' },
        },
      },
    },
  },
  plugins: [],
}
