/* ============================================================
   v2.1 拆分:全站公共核心(7 个前台页面都先加载这个)
   - esc / escAttr:HTML 转义(全局 const,后续脚本直接用)
   - 汉堡菜单、滚动/技能条/数字动画的观察器
   - 返回顶部、微信二维码弹窗
   ============================================================ */
'use strict';

const esc = s => { const d = document.createElement('div'); d.textContent = s ?? ''; return d.innerHTML; };
// 放进 HTML 属性(双引号包裹)时用这个:额外转义引号,防属性逃逸
const escAttr = s => esc(s).replace(/"/g, '&quot;').replace(/'/g, '&#39;');

// ===== v3.2.1:禁用右键菜单(前台访客侧;后台不加载 core.js 不受影响) =====
document.addEventListener('contextmenu', e => e.preventDefault());

// ===== 移动端汉堡菜单 =====
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
  navLinks.querySelectorAll('a').forEach(a =>
    a.addEventListener('click', () => navLinks.classList.remove('open'))
  );
}

// ===== 滚动渐入显现 =====
const io = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
  });
}, { threshold: 0.12 });
const observeReveals = root => (root || document).querySelectorAll('.reveal')
  .forEach(el => io.observe(el));
observeReveals();

// ===== 技能条动画(滚到可视区域时填充) =====
const barIO = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); barIO.unobserve(e.target); }
  });
}, { threshold: 0.4 });
const observeSkillbars = () => document.querySelectorAll('.skillbar').forEach(el => barIO.observe(el));
observeSkillbars();

// ===== 数字滚动动画 =====
const counterIO = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (!e.isIntersecting) return;
    const el = e.target;
    const target = parseInt(el.dataset.count, 10);
    const dur = 1100, t0 = performance.now();
    const tick = now => {
      const p = Math.min((now - t0) / dur, 1);
      el.textContent = Math.round(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
    counterIO.unobserve(el);
  });
}, { threshold: 0.5 });
const observeCounters = () => document.querySelectorAll('[data-count]').forEach(el => counterIO.observe(el));
observeCounters();

// ===== 返回顶部按钮 =====
const backTop = document.getElementById('backTop');
if (backTop) {
  window.addEventListener('scroll', () => {
    backTop.classList.toggle('show', window.scrollY > 480);
  }, { passive: true });
  backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

// ===== 微信二维码弹窗 =====
const qrOverlay = document.getElementById('qrOverlay');
const wechatBtn = document.getElementById('wechatBtn');
const qrClose = document.getElementById('qrClose');
if (qrOverlay && wechatBtn) {
  const closeQr = () => qrOverlay.classList.remove('open');
  wechatBtn.addEventListener('click', e => {
    e.preventDefault();
    qrOverlay.classList.add('open');
  });
  if (qrClose) qrClose.addEventListener('click', closeQr);
  qrOverlay.addEventListener('click', e => { if (e.target === qrOverlay) closeQr(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeQr(); });
}
