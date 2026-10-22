/* ============================================================
   我的小窝 · 页面数据脚本(v2.1 拆分后只剩"拉数据渲染"这一件事)
   依赖:js/core.js 先加载(用到 esc/escAttr 与观察器)
   从后台拉当前页面用到的数据(技能树/时间线/统计等),
   拉取失败(本地打开/后台挂了)就用页面内置内容兜底
   ============================================================ */
'use strict';

console.log('%c 嗨!你打开了控制台,是想看看这个网页的秘密吗 👀', 'font-size:14px;color:#ff6b9d;font-weight:bold;');

// 每个页面拉哪个接口:map 只有站点信息
const PAGE_API = {
  index: '/api/page/index',
  about: '/api/page/about',
  skills: '/api/page/skills',
  works: '/api/page/works',
  campus: '/api/page/campus',
  contact: '/api/page/contact',
  map: '/api/page/map',
};

/* ---------- v2.5 站点信息套用 ----------
   后台「站点信息」里改的姓名/站名/学校/专业/年级/方向/标语/版权,
   在这里替换到前台各页。静态 HTML 里保留原值作兜底,
   接口拿不到(本地打开/后台挂)就什么都不动。 */
function applySite(s) {
  const owner = s.site_owner || '';
  const ORIG_OWNER = '至尊杰';
  const ORIG_NAME = '至尊杰的小窝';
  // 站名还是默认值(含旧姓名)时,跟着姓名一起变,避免"张三的小窝"里还写着至尊杰
  let name = s.site_name || '';
  if (!name || name === ORIG_NAME) name = owner + '的小窝';
  const school = s.site_school || '';
  const major = s.site_major || '';
  const grade = s.site_grade || '';
  const focus = s.site_focus || '';
  const slogan = s.site_slogan || '';
  const credit = s.site_credit || '';
  const year = s.site_start_year || '';

  // 1) 打标记的元素
  const set = (sel, txt) => document.querySelectorAll(sel).forEach(el => { el.textContent = txt; });
  set('[data-site="site_name"]', name);
  set('[data-site="owner"]', ' ' + owner + ' ');
  set('[data-site="focus"]', focus);
  if (owner) set('[data-site="badge"]', `🎓 ${school} · ${major} · ${grade}`);

  // 2) 页脚版权整行
  const foot = document.querySelector('[data-site="footer"]');
  if (foot) {
    const sprout = foot.querySelector('.sprout');
    foot.textContent = `© ${year} ${owner} · ${school} · ${credit} · ${slogan} `;
    if (sprout) foot.appendChild(sprout);
  }

  // 3) <title>:把「某某的小窝」和姓名换掉
  const origName = '至尊杰';
  if (document.title) {
    let t = document.title.replace(/[^·]+的小窝/g, name);
    t = t.replace(new RegExp(origName, 'g'), owner);
    document.title = t;
  }

  // 4) SEO / 社交 meta(description 里也含姓名和站名,一并换)
  const metaSet = (sel, val) => {
    const el = document.querySelector(sel);
    if (el && val) el.setAttribute('content', val);
  };
  metaSet('meta[name="author"]', owner);
  metaSet('meta[property="og:site_name"]', name);
  metaSet('meta[property="og:image:alt"]', name + ' —— ' + slogan);
  metaSet('meta[property="og:title"]', document.title);
  metaSet('meta[name="twitter:title"]', document.title);

  // description 类:做全局文本替换(姓名 + 站名 + 学校/专业)
  ['meta[name="description"]', 'meta[property="og:description"]',
   'meta[name="twitter:description"]'].forEach(sel => {
    const el = document.querySelector(sel);
    if (!el) return;
    let v = el.getAttribute('content') || '';
    v = v.replace(new RegExp(origName + '的小窝', 'g'), name)
         .replace(new RegExp(origName, 'g'), owner)
         .replace(/燕京理工学院/g, school);
    el.setAttribute('content', v);
  });

  // 5) 页面上所有纯文本节点:用 TreeWalker 逐个替换,
  //    这样 <p><strong>是谁:</strong>至尊杰,...</p> 这种混合结构也能改到
  if (owner && owner !== ORIG_OWNER) {
    const re = new RegExp(ORIG_OWNER, 'g');
    const walker = document.createTreeWalker(
      document.body, NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const p = node.parentElement;
          if (!p) return NodeFilter.FILTER_REJECT;
          const tag = p.tagName;
          if (tag === 'SCRIPT' || tag === 'STYLE' || tag === 'TEXTAREA') {
            return NodeFilter.FILTER_REJECT;
          }
          return node.nodeValue.includes(ORIG_OWNER)
            ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
        },
      });
    const hits = [];
    while (walker.nextNode()) hits.push(walker.currentNode);
    hits.forEach(n => { n.nodeValue = n.nodeValue.replace(re, owner); });

    // 图片 alt 属性
    document.querySelectorAll('img[alt]').forEach(img => {
      if (img.alt.includes(ORIG_OWNER)) img.alt = img.alt.replace(re, owner);
    });
  }

  // 6) JSON-LD 结构化数据
  const ld = document.querySelector('script[type="application/ld+json"]');
  if (ld) {
    try {
      const j = JSON.parse(ld.textContent);
      if (j.name) j.name = owner;
      if (j.description) {
        j.description = j.description
          .replace(new RegExp(ORIG_OWNER, 'g'), owner)
          .replace(/燕京理工学院/g, school);
      }
      ld.textContent = JSON.stringify(j, null, 2);
    } catch (e) {}
  }

  // 记住替换规则,动态渲染出来的内容(自我介绍/时间线等)渲染完再扫一遍
  window.__SITE_OWNER__ = owner;
  window.__SITE_ORIG_OWNER__ = ORIG_OWNER;
}

/* 动态内容渲染完后再替换一遍姓名(自我介绍段落是异步渲染的,
   首轮 applySite 时它还没进 DOM) */
function rescanOwner() {
  const owner = window.__SITE_OWNER__;
  const orig = window.__SITE_ORIG_OWNER__;
  if (!owner || !orig || owner === orig) return;
  const re = new RegExp(orig, 'g');
  const walker = document.createTreeWalker(
    document.body, NodeFilter.SHOW_TEXT, {
      acceptNode(node) {
        const p = node.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        if (['SCRIPT', 'STYLE', 'TEXTAREA'].includes(p.tagName)) {
          return NodeFilter.FILTER_REJECT;
        }
        return node.nodeValue.includes(orig)
          ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      },
    });
  const hits = [];
  while (walker.nextNode()) hits.push(walker.currentNode);
  hits.forEach(n => { n.nodeValue = n.nodeValue.replace(re, owner); });
}


// v2.2 荣誉等级 → 展示标签
const HONOR_LEVEL_LABEL = {
  national: '国家级', provincial: '省级', school: '校级', other: '其他',
};
const HONOR_LEVEL_CLS = {
  national: 'hl-national', provincial: 'hl-provincial',
  school: 'hl-school', other: 'hl-other',
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

  // ---- v2.5 站点信息(每页都套用) ----
  if (data.site) applySite(data.site);

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

  // ---- v2.2 荣誉墙(about 页) ----
  if (Array.isArray(data.honors) && data.honors.length) {
    const box = document.getElementById('honorWall');
    if (box) {
      box.innerHTML = data.honors.map((h, i) => `
        <div class="honor-card reveal d${i % 3} ${HONOR_LEVEL_CLS[h.level] || 'hl-school'}">
          <div class="honor-top">
            <span class="honor-emoji">${esc(h.emoji)}</span>
            <span class="honor-level">${esc(HONOR_LEVEL_LABEL[h.level] || h.level)}</span>
          </div>
          <div class="honor-year">${esc(h.year)}</div>
          <h3 class="honor-title">${esc(h.title)}</h3>
          ${h.desc ? `<p class="honor-desc">${esc(h.desc)}</p>` : ''}
        </div>`).join('');
      observeReveals();
    }
  }

  // ---- v2.2 随手记(campus 页) ----
  if (Array.isArray(data.notes) && data.notes.length) {
    const box = document.getElementById('noteWall');
    if (box) {
      box.innerHTML = data.notes.map((n, i) => `
        <div class="note-card note-${esc(n.mood || 'teal')} reveal d${i % 3}">
          <span class="note-emoji">${esc(n.emoji)}</span>
          <p class="note-text">${esc(n.text)}</p>
          <span class="note-date">${fmtNoteDate(n.ts)}</span>
        </div>`).join('');
      observeReveals();
    }
  }

  // ---- v2.2 友情链接(contact 页) ----
  if (Array.isArray(data.friendlinks) && data.friendlinks.length) {
    const box = document.getElementById('friendLinks');
    if (box) {
      box.innerHTML = data.friendlinks.map((f, i) => `
        <a class="friend-card reveal d${i % 3}" href="${escAttr(f.url)}"
           target="_blank" rel="noopener noreferrer">
          <span class="friend-emoji">${esc(f.emoji)}</span>
          <span class="friend-info">
            <b class="friend-name">${esc(f.name)}</b>
            ${f.desc ? `<span class="friend-desc">${esc(f.desc)}</span>` : ''}
          </span>
          <span class="friend-go">→</span>
        </a>`).join('');
      observeReveals();
    }
  }

  // ---- v2.4 最近在听(about 页) ----
  if (Array.isArray(data.songs) && data.songs.length) {
    const box = document.getElementById('musicList');
    if (box) {
      box.innerHTML = data.songs.map((s, i) => `
        <div class="music-card reveal d${i % 3}">
          <div class="music-head">
            <span class="music-emoji">${esc(s.emoji || '🎵')}</span>
            <span class="music-meta">
              <b class="music-title">${esc(s.title)}</b>
              <span class="music-artist">${esc(s.artist || '未知歌手')}</span>
            </span>
          </div>
          ${s.note ? `<p class="music-note">${esc(s.note)}</p>` : ''}
          <iframe class="music-frame" loading="lazy"
                  src="https://i.y.qq.com/n2/m/outchain/player/index.html?songid=${encodeURIComponent(s.song_id)}"
                  frameborder="0" allow="autoplay" title="QQ音乐播放器:${escAttr(s.title)}"></iframe>
        </div>`).join('');
      observeReveals();
    }
  }

  // 动态内容都渲染完了,再扫一遍姓名(自我介绍/时间线里可能有硬编码姓名)
  rescanOwner();
}

// 随手记时间:同天显示「今天 HH:MM」,当年显示「M月D日」,否则「YYYY.M.D」
function fmtNoteDate(ts) {
  try {
    const d = new Date(ts * 1000), now = new Date();
    const hm = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
    if (d.toDateString() === now.toDateString()) return '今天 ' + hm;
    const md = (d.getMonth() + 1) + '月' + d.getDate() + '日';
    return d.getFullYear() === now.getFullYear() ? md : d.getFullYear() + '.' + (d.getMonth() + 1) + '.' + d.getDate();
  } catch (e) { return ''; }
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
