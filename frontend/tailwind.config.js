/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        // 沿用原站贴纸风配色,保证视觉延续
        cream: 'var(--cream)',
        paper: 'var(--paper)',
        ink: 'var(--ink)',
        pink: { DEFAULT: 'var(--pink)', bg: 'var(--pink-bg)' },
        yellow: { DEFAULT: 'var(--yellow)', bg: 'var(--yellow-bg)' },
        teal: { DEFAULT: 'var(--teal)', bg: 'var(--teal-bg)' },
        purple: { DEFAULT: 'var(--purple)', bg: 'var(--purple-bg)' },
        orange: { DEFAULT: 'var(--orange)', bg: 'var(--orange-bg)' },
        blue: { DEFAULT: 'var(--blue)', bg: 'var(--blue-bg)' },
        shadow: 'var(--shadow)',
        rule: 'var(--rule)',
      },
      fontFamily: {
        round: ['"ZCOOL KuaiLe"', '"Baloo 2"', 'system-ui', 'sans-serif'],
        sans: ['"Baloo 2"', '"PingFang SC"', '"Microsoft YaHei"', 'sans-serif'],
      },
      boxShadow: {
        sticker: '4px 4px 0 var(--shadow)',
        'sticker-lg': '6px 6px 0 var(--shadow)',
        'sticker-sm': '2px 2px 0 var(--shadow)',
      },
      borderRadius: { sticker: '18px' },
    },
  },
  plugins: [],
};
