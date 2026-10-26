import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';

/**
 * 前台入口。
 * 页面由 Flask 渲染的 HTML 提供 <div id="react-root" data-page="...">,
 * 这里只接管该容器,其余(head 里的 meta)保持服务端输出。
 */
const el = document.getElementById('react-root');
if (el) {
  createRoot(el).render(
    <React.StrictMode>
      <App initialPage={el.dataset.page || 'index'} />
    </React.StrictMode>
  );
}
