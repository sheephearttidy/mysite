/* ============================================================
   我的小窝 · 页面数据脚本(v2.1 拆分后只剩"拉数据渲染"这一件事)
   依赖:js/core.js 先加载(用到 esc/escAttr 与观察器)
   从后台拉当前页面用到的数据(技能树/时间线/统计等),
   拉取失败(本地打开/后台挂了)就用页面内置内容兜底
   ============================================================ */
'use strict';

console.log('%c 嗨!你打开了控制台,是想看看这个网页的秘密吗 👀', 'font-size:14px;color:#ff6b9d;font-weight:bold;');

// 每个页面拉哪个接口:contact 没有动态数据,直接跳过
const PAGE_API = {
  index: '/api/page/index',
  about: '/api/page/about',
  skills: '/api/page/skills',
  works: '/api/page/works',
  campus: '/api/page/campus',
  map: '/api/page/map',
};

async function loadDynamicContent() {
  const page = document.body.dataset.page || 'index';
  const api = PAGE_API[page];
  if (!api) return;

  let data;
  try {
    const res = await fetch(api);
    if (!res.ok) return;
    data = await res.json();
  } catch { return; }   // 本地 file:// 打开或后台不在线,静默回退

  // ---- 技能树 ----
  if (Array.isArray(data.skills) && data.skills.length) {
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

  // ---- 项目墙(封面底色键与 API/后台一致: pink/yellow/teal/purple/orange/blue) ----
  if (Array.isArray(data.works) && data.works.length) {
    const grid = document.getElementById('worksGrid');
    if (grid) {
      grid.innerHTML = data.works.map((w, i) => `
        <article class="card work-card reveal d${i % 3}">
          <div class="work-cover wc-${escAttr(w.cover)}">${esc(w.emoji)}</div>
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

  // v1.10:新老访客标识(localStorage 匿名标志,不含任何个人信息)
  let isNew = true;
  try {
    isNew = !localStorage.getItem('mysite_seen');
    localStorage.setItem('mysite_seen', '1');
  } catch (e) { isNew = true; }

  const payload = JSON.stringify({ path: location.pathname, is_new: isNew });
  let vid = 0;
  const t0 = Date.now();

  // v1.10:停留时长补报(切走/关闭时发;重复发无害,后端取 MAX)
  function reportDur() {
    if (!vid) return;
    const dur = Math.round((Date.now() - t0) / 1000);
    if (dur < 1) return;
    const body = JSON.stringify({ vid, dur_s: dur });
    try {
      if (navigator.sendBeacon) {
        navigator.sendBeacon('/api/track/dur',
          new Blob([body], { type: 'application/json' }));
        return;
      }
    } catch (e) {}
    fetch('/api/track/dur', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body, keepalive: true,
    }).catch(() => {});
  }
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) reportDur();
  });
  window.addEventListener('pagehide', reportDur);

  // 统一用 fetch(拿到 vid 才能补报停留时长)
  fetch('/api/track', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: payload,
    keepalive: true,
  }).then(r => r.json()).then(d => { vid = d.vid || 0; }).catch(() => {});
})();
