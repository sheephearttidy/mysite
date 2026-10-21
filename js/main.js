/* ============================================================
   我的小窝 · 交互脚本
   负责所有动效:菜单、滚动显现、技能条、数字滚动、返回顶部
   改内容请去 index.html,一般不用动这个文件
   ============================================================ */

console.log('%c 嗨!你打开了控制台,是想看看这个网页的秘密吗 👀', 'font-size:14px;color:#ff6b9d;font-weight:bold;');

// ===== 移动端汉堡菜单 =====
const navToggle = document.getElementById('navToggle');
const navLinks = document.getElementById('navLinks');
navToggle.addEventListener('click', () => navLinks.classList.toggle('open'));
navLinks.querySelectorAll('a').forEach(a =>
  a.addEventListener('click', () => navLinks.classList.remove('open'))
);

// ===== 滚动渐入显现 =====
const io = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); io.unobserve(e.target); }
  });
}, { threshold: 0.12 });
document.querySelectorAll('.reveal').forEach(el => io.observe(el));

// ===== 技能条动画(滚到可视区域时填充) =====
const barIO = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) { e.target.classList.add('visible'); barIO.unobserve(e.target); }
  });
}, { threshold: 0.4 });
document.querySelectorAll('.skillbar').forEach(el => barIO.observe(el));

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
document.querySelectorAll('[data-count]').forEach(el => counterIO.observe(el));

// ===== 返回顶部按钮 =====
const backTop = document.getElementById('backTop');
window.addEventListener('scroll', () => {
  backTop.classList.toggle('show', window.scrollY > 480);
}, { passive: true });
backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// ===== 微信二维码弹窗 =====
const qrOverlay = document.getElementById('qrOverlay');
const wechatBtn = document.getElementById('wechatBtn');
const qrClose = document.getElementById('qrClose');
const closeQr = () => qrOverlay.classList.remove('open');
wechatBtn.addEventListener('click', e => {
  e.preventDefault();
  qrOverlay.classList.add('open');
});
qrClose.addEventListener('click', closeQr);
qrOverlay.addEventListener('click', e => { if (e.target === qrOverlay) closeQr(); });
document.addEventListener('keydown', e => { if (e.key === 'Escape') closeQr(); });
