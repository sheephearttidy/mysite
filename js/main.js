/* ============================================================
   我的小窝 · 交互脚本
   负责所有动效:菜单、滚动显现、技能条、数字滚动、返回顶部
   另外负责从后台 API 拉取技能树/时间线/统计(拉不到就用页面内置内容)
   ============================================================ */

console.log('%c 嗨!你打开了控制台,是想看看这个网页的秘密吗 👀', 'font-size:14px;color:#ff6b9d;font-weight:bold;');

// ===== 工具:HTML 转义 =====
const esc = s => { const d = document.createElement('div'); d.textContent = s ?? ''; return d.innerHTML; };
// 放进 HTML 属性(双引号包裹)时用这个:额外转义引号,防属性逃逸
const escAttr = s => esc(s).replace(/"/g, '&quot;').replace(/'/g, '&#39;');

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
const observeReveals = root => document.querySelectorAll('.reveal').forEach(el => io.observe(el));
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
window.addEventListener('scroll', () => {
  backTop.classList.toggle('show', window.scrollY > 480);
}, { passive: true });
backTop.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));

// ===== 深色模式 =====
// 主题切换逻辑在 js/theme.js 里(前后台共用同一个文件),这里不用重复实现

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

// ============================================================
// 动态内容:从后台拉取技能树 / 时间线 / 统计数据
// 拉取失败(本地打开 / 后台挂了)就什么都不做,页面内置内容兜底
// ============================================================

async function loadDynamicContent() {
  let data;
  try {
    const res = await fetch('/api/content');
    if (!res.ok) return;
    data = await res.json();
  } catch { return; }   // 本地 file:// 打开或后台不在线,静默回退

  // ---- 技能树 ----
  if (Array.isArray(data.skills) && data.skills.length) {
    const cols = { serious: document.querySelector('.skills-cols .col-a .skillbar')?.parentElement, passive: null };
    const colA = document.querySelector('.skills-cols .col-a');
    const colB = document.querySelector('.skills-cols .col-b');
    if (colA && colB) {
      const render = s => `
        <div class="skillbar" style="--w:${s.percent}%">
          <div class="skillbar-top"><span>${esc(s.name)}</span><span class="pct">${s.percent}%</span></div>
          <div class="bar"><div class="fill f-${esc(s.color)}"></div></div>
          ${s.note ? `<div class="note">${esc(s.note)}</div>` : ''}
        </div>`;
      colA.innerHTML = '<h3>📖 认真技能</h3><p class="sub">真的在学的那种</p>' +
        data.skills.filter(s => s.category === 'serious').map(render).join('');
      colB.innerHTML = '<h3>🎮 被动技能</h3><p class="sub">不用学,天生就会</p>' +
        data.skills.filter(s => s.category === 'passive').map(render).join('');
      observeSkillbars();
    }
  }

  // ---- 趣味统计 ----
  if (Array.isArray(data.stats) && data.stats.length) {
    const statsBox = document.querySelector('.stats');
    if (statsBox) {
      statsBox.innerHTML = data.stats.map((s, i) => `
        <div class="stat reveal d${(i % 4) + 1}">
          <span class="emoji">${esc(s.emoji)}</span>
          <div class="num-row"><span data-count="${s.number}">0</span><span class="unit"> ${esc(s.unit)}</span></div>
          <div class="label">${esc(s.label)}</div>
        </div>`).join('');
      observeCounters();
      observeReveals();
    }
  }

  // ---- 校园时间线 ----
  if (Array.isArray(data.timeline) && data.timeline.length) {
    const tl = document.querySelector('.timeline');
    if (tl) {
      tl.innerHTML = data.timeline.map(e => `
        <div class="tl-item reveal" data-emoji="${escAttr(e.emoji)}">
          <div class="card tl-card">
            <span class="time">${esc(e.time_label)}</span>
        <h3>${esc(e.title)}</h3>
        <p>${esc(e.content)}</p>
          </div>
        </div>`).join('');
      observeReveals();
    }
  }

  // ---- 项目墙 ----
  if (Array.isArray(data.works) && data.works.length) {
    const grid = document.getElementById('worksGrid');
    if (grid) {
      grid.innerHTML = data.works.map((w, i) => `
        <article class="card work-card reveal d${i % 3}">
          <div class="work-cover cover-${escAttr(w.cover)}">${esc(w.emoji)}</div>
          <div class="work-body">
            <h3>${esc(w.title)}</h3>
            <p>${esc(w.desc)}</p>
            <div class="work-meta">
              <span class="work-pill">${esc(w.pill)}</span>
              ${w.link ? `<a href="${escAttr(w.link)}" class="link" target="_blank" rel="noopener noreferrer">去看看 →</a>` : ''}
            </div>
          </div>
        </article>`).join('');
      observeReveals();
    }
  }

  // ---- 关于我(自我介绍段落 + 信息卡片) ----
  if (Array.isArray(data.profile) && data.profile.length) {
    const abouts = data.profile.filter(p => p.kind === 'about');
    const infos = data.profile.filter(p => p.kind === 'info');

    const aboutCard = document.getElementById('aboutCard');
    if (aboutCard && abouts.length) {
      aboutCard.innerHTML = abouts.map(p =>
        `<p><strong>${esc(p.label)}:</strong>${esc(p.value)}</p>`).join('');
    }

    const infoBox = document.getElementById('infoCards');
    if (infoBox && infos.length) {
      infoBox.innerHTML = infos.map((p, i) => `
        <div class="info-card reveal d${i % 4}">
          <span class="ic">${esc(p.emoji)}</span>
          <div class="k">${esc(p.label)}</div>
          <div class="v">${esc(p.value)}</div>
        </div>`).join('');
      observeReveals();
    }
  }
}
loadDynamicContent();

/* ================= 访问统计上报 ================= */
(function trackVisit() {
  // 同一标签页一次会话只报一次,避免刷新刷量
  try {
    if (sessionStorage.getItem('tracked')) return;
    sessionStorage.setItem('tracked', '1');
  } catch (e) { /* 隐私模式下 sessionStorage 可能不可用,照常上报 */ }

  // 用 sendBeacon 最不打扰;不支持就退回 fetch
  const payload = JSON.stringify({ path: location.pathname });
  try {
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/track',
        new Blob([payload], { type: 'application/json' }));
      return;
    }
  } catch (e) {}
  fetch('/api/track', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: payload,
    keepalive: true,
  }).catch(() => {});
})();
