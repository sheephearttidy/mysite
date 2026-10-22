/* ============================================================
   后台 · admin-core:全局工具与渲染入口(v2.1 拆分)
   toast / api / esc / escAttr / renderAll
   说明:顶层 const/function 跨 <script> 共享,后续模块直接使用
   ============================================================ */
'use strict';/* ============================================================
   我的小窝 · 后台管理脚本
   数据由 admin.html 里的内联 <script> 通过 window 传入,
   所以这个文件是纯静态的,不经过 Jinja 渲染。
   ============================================================ */
const DATA = window.__ADMIN_DATA__ || {};
// 技能条颜色交给 CSS 的 .bf-* 类,深色模式才能跟着一起变
const CATS = { serious: '认真技能', passive: '被动技能' };

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 1800);
}

async function api(method, path, body) {
  const opt = { method, headers: {'Content-Type':'application/json'} };
  if (body) opt.body = JSON.stringify(body);
  const res = await fetch(path, opt);
  if (res.status === 401) { location.href = '/admin/login'; throw new Error('unauthorized'); }
  if (!res.ok && res.status !== 204) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.error || res.status);
  }
  return res.status === 204 ? null : res.json();
}

function esc(s) { const d = document.createElement('div'); d.textContent = s ?? ''; return d.innerHTML; }
// 属性值(双引号包裹)专用:额外转义引号,防 " 逃逸出属性
function escAttr(s) { return esc(s).replace(/"/g, '&quot;').replace(/'/g, '&#39;'); }

/* ---------- 列表渲染 ---------- */
function renderAll() {
  renderSkills(); renderTimeline(); renderStats();
  renderWorks(); renderProfile();
  updateCounts();
}
