import React from 'react';
import { createRoot } from 'react-dom/client';
import AdminApp from './admin/AdminApp.jsx';

/**
 * 后台入口。
 * 后台仍是表单密集型页面,这里先挂载 React 根,
 * 后续逐个面板迁移过去(见 src/admin/)。
 */
const el = document.getElementById('admin-react-root');
if (el) {
  const data = window.__ADMIN_DATA__ || {};
  createRoot(el).render(
    <React.StrictMode>
      <AdminApp initialData={data} />
    </React.StrictMode>
  );
}
