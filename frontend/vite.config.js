import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

/**
 * 我的小窝 · React 前端构建配置
 *
 * 设计要点:
 * 1. 产物直接输出到 ../static-react/,由 Flask 的 send_from_directory 托管,
 *    不依赖 nginx 改配置(现有 location / 已反代给 Flask)。
 * 2. 多入口:front(前台)+ admin-sidebar(后台侧边栏菜单),各自独立打包。
 * 3. 不生成 sourcemap(生产不需要,还省体积)。
 * 4. 资源文件名带内容哈希,配合长缓存。
 */
export default defineConfig({
  plugins: [react()],
  base: '/static-react/',
  build: {
    outDir: resolve(__dirname, '../static-react'),
    emptyOutDir: true,
    sourcemap: false,
    manifest: 'manifest.json',
    rollupOptions: {
      input: {
        front: resolve(__dirname, 'src/main.jsx'),
        'admin-sidebar': resolve(__dirname, 'src/admin-sidebar.jsx'),
      },
      output: {
        entryFileNames: 'assets/[name]-[hash].js',
        chunkFileNames: 'assets/[name]-[hash].js',
        assetFileNames: 'assets/[name]-[hash][extname]',
      },
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:5100',
    },
  },
});
