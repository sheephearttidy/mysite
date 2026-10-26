import React from 'react';
import { createRoot } from 'react-dom/client';
import AdminSidebar from './admin/AdminSidebar.jsx';

/**
 * 后台侧边栏入口(v4.2.0)。
 *
 * 只接管侧边栏菜单这一块:渲染 BranchedMenu 多级菜单,
 * 点击时调用原有的 showPanel()(全局函数),从而复用现有 27 个面板的实现。
 * 这样既用上了新组件,又不用重写整个后台。
 */
const el = document.getElementById('admin-sidebar-root');
if (el) {
  createRoot(el).render(
    <React.StrictMode>
      <AdminSidebar
        initialPanel={el.dataset.panel || 'skills'}
        onNavigate={(id) => {
          // 交给原有后台逻辑切换面板(它负责面板显示、标题、面包屑)
          if (typeof window.showPanel === 'function') window.showPanel(id);
        }}
      />
    </React.StrictMode>
  );
}
