import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

/**
 * 构建配置
 *
 * - 多入口:index.html(前台 SPA) + admin.html(后台)
 * - 产物输出到 dist/,生产由 nginx 直出静态文件,FastAPI 只提供 /api
 * - 开发时 /api 代理到本地 FastAPI(5100)
 */
export default defineConfig({
  plugins: [react()],
  base: '/',
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: false,
    target: 'es2020',
    rollupOptions: {
      input: {
        main: resolve(__dirname, 'index.html'),
        admin: resolve(__dirname, 'admin.html'),
      },
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
        },
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5100',
      '/assets/uploads': 'http://127.0.0.1:5100',
    },
  },
});
