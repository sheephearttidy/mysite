/**
 * 后台入口:独立挂载,不进前台 SPA 路由。
 */
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { AdminApp } from './admin/AdminApp';
import './index.css';

const el = document.getElementById('root');
if (!el) throw new Error('#root not found');

createRoot(el).render(
  <StrictMode>
    <AdminApp />
  </StrictMode>,
);
