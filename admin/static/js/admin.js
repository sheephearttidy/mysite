/* ============================================================
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

/* ---------- 侧边栏导航 ---------- */
const PANELS = {
  'skills':        { title:'🎯 技能树管理',    crumb:'内容管理 / 技能树' },
  'timeline':      { title:'🗺️ 校园日常管理',  crumb:'内容管理 / 校园日常' },
  'stats':         { title:'🧮 趣味统计管理',  crumb:'内容管理 / 趣味统计' },
  'works':         { title:'🛠️ 项目墙管理',    crumb:'内容管理 / 项目墙' },
  'messages':      { title:'✉️ 留言板',        crumb:'内容管理 / 留言板' },
  'profile-about': { title:'✍️ 自我介绍段落',  crumb:'个人信息 / 自我介绍' },
  'profile-info':  { title:'🪪 信息卡片',      crumb:'个人信息 / 信息卡片' },
  'uploads':       { title:'🖼️ 图片库',        crumb:'媒体资源 / 图片库' },
  'dashboard':     { title:'📊 数据看板',      crumb:'站点维护 / 数据看板' },
  'fx':            { title:'🎉 前台特效',      crumb:'站点维护 / 前台特效' },
  'backup':        { title:'💾 数据备份',      crumb:'站点维护 / 数据备份' },
  'likes':         { title:'❤️ 点赞统计',      crumb:'站点维护 / 点赞统计' },
  'notices':       { title:'📢 站点公告',      crumb:'站点维护 / 站点公告' },
  'countdown':     { title:'⏳ 倒计时',        crumb:'站点维护 / 倒计时' },
  'sec-pass':      { title:'🔑 后台密码',      crumb:'安全中心 / 后台密码' },
  'sec-login':     { title:'🛡️ 登录防护',      crumb:'安全中心 / 登录防护' },
  'sec-blocked':   { title:'⛔ 封锁名单',      crumb:'安全中心 / 封锁名单' },
  'sec-sessions':  { title:'💻 登录会话',      crumb:'安全中心 / 登录会话' },
  'sec-audit':     { title:'📜 审计日志',      crumb:'安全中心 / 审计日志' },
  'sec-status':    { title:'🛡️ 防护状态',      crumb:'安全中心 / 防护状态' },
};

const SEC_PANELS = ['sec-pass', 'sec-login', 'sec-blocked', 'sec-sessions', 'sec-audit', 'sec-status'];

function showPanel(name) {
  if (!PANELS[name]) name = 'skills';
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  const el = document.getElementById('panel-' + name);
  if (el) el.classList.add('active');

  document.querySelectorAll('.sb-link').forEach(a =>
    a.classList.toggle('active', a.dataset.panel === name));

  document.getElementById('panelTitle').textContent = PANELS[name].title;
  document.getElementById('panelCrumb').textContent = PANELS[name].crumb;

  // 看板:每次进来都刷新一次数据
  if (name === 'dashboard') loadDashboard(DASH_DAYS);

  // 前台特效面板:读取当前设置
  if (name === 'fx') loadFxSettings();

  // 留言板 / 点赞:按需刷新
  if (name === 'messages') loadMessages();
  if (name === 'likes') loadLikes();
  if (name === 'notices') loadNotices();
  if (name === 'countdown') loadCountdowns();

  // 安全中心各子面板:按需刷新对应数据
  if (SEC_PANELS.includes(name)) {
    loadSecOverview();
    if (name === 'sec-audit') loadAudit();
  }

  // 图片库:每次进来刷新列表
  if (name === 'uploads' && typeof loadUploads === 'function') loadUploads();

  // 记住当前面板
  try { localStorage.setItem('admin_panel', name); } catch (e) {}
  // 小屏切面板后收起抽屉
  closeSidebar();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

document.querySelectorAll('.sb-link').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    showPanel(a.dataset.panel);
    history.replaceState(null, '', '#' + a.dataset.panel);
  });
});

// 分组折叠
function toggleGroup(btn) {
  btn.parentElement.classList.toggle('collapsed');
  saveGroups();
}
function saveGroups() {
  const state = {};
  document.querySelectorAll('.sb-group').forEach(g => {
    state[g.dataset.group] = g.classList.contains('collapsed');
  });
  try { localStorage.setItem('admin_groups', JSON.stringify(state)); } catch (e) {}
}
function restoreGroups() {
  try {
    const state = JSON.parse(localStorage.getItem('admin_groups') || '{}');
    document.querySelectorAll('.sb-group').forEach(g => {
      if (state[g.dataset.group]) g.classList.add('collapsed');
    });
  } catch (e) {}
}

// 移动端抽屉
const sidebar = document.getElementById('sidebar');
const sbScrim = document.getElementById('sbScrim');
document.getElementById('sbToggle').addEventListener('click', () => {
  sidebar.classList.toggle('open');
  sbScrim.classList.toggle('show', sidebar.classList.contains('open'));
});
sbScrim.addEventListener('click', closeSidebar);
function closeSidebar() {
  sidebar.classList.remove('open');
  sbScrim.classList.remove('show');
}

// 数量角标
function updateCounts() {
  const set = (id, n) => {
    const el = document.getElementById(id);
    if (el) el.textContent = n;
  };
  set('cnt-skills', DATA.skills.length);
  set('cnt-timeline', DATA.timeline.length);
  set('cnt-stats', DATA.stats.length);
  set('cnt-works', DATA.works.length);
  set('cnt-about', DATA.profile.filter(p => p.kind === 'about').length);
  set('cnt-info', DATA.profile.filter(p => p.kind === 'info').length);
}

/* ---------- 前台特效面板 ---------- */
const FX_KEY_LABEL = {
  'national-day': '🇨🇳 国庆节(红旗)',
  'valentine': '💗 情人节(爱心)',
  'memorial': '🕯️ 国家公祭日(全站黑白)',
  'new-year': '🎆 元旦(彩带)',
  'christmas': '🎄 圣诞节(雪花)',
  'labor': '🧹 劳动节(彩带)',
  'children': '✈️ 儿童节(纸飞机)',
  'teacher': '⭐ 教师节(星星)',
};

async function loadFxSettings() {
  try {
    const d = await api('GET', '/api/security/fx');
    const s = d.settings || d;
    const mode = s.fx_holiday_mode || 'auto';

    document.getElementById('fxHolidayOn').checked = mode !== 'off';
    document.getElementById('fxMode').value = mode;
    document.getElementById('fxKey').value = s.fx_holiday_key || '';
    document.getElementById('fxEffects').checked = s.fx_effects !== '0';
    updateFxKeyDisabled();
  } catch (e) { toast('特效设置加载失败:' + e.message); }
}

function updateFxKeyDisabled() {
  const mode = document.getElementById('fxMode').value;
  const on = document.getElementById('fxHolidayOn').checked;
  document.getElementById('fxKey').disabled = (mode !== 'manual') || !on;
}

async function saveFxSettings() {
  const on = document.getElementById('fxHolidayOn').checked;
  let mode = document.getElementById('fxMode').value;
  if (!on) mode = 'off';

  const body = {
    fx_holiday_mode: mode,
    fx_holiday_key: mode === 'manual' ? document.getElementById('fxKey').value : '',
    fx_effects: document.getElementById('fxEffects').checked ? '1' : '0',
  };
  try {
    await api('POST', '/api/security/fx', body);
    toast('✅ 特效设置已保存,前台刷新即可生效');
    loadFxSettings();
  } catch (e) { toast('保存失败:' + e.message); }
}

function previewFx() {
  const box = document.getElementById('fxPreview');
  const mode = document.getElementById('fxMode').value;
  const on = document.getElementById('fxHolidayOn').checked;
  const key = document.getElementById('fxKey').value;

  if (!on || mode === 'off') {
    box.innerHTML = '<p class="hint">当前:全部关闭,前台不会出现任何节日特效。</p>';
    return;
  }
  if (mode === 'manual') {
    if (!key) {
      box.innerHTML = '<p class="hint">手动模式但没选节日 → 前台不会显示特效。</p>';
      return;
    }
    box.innerHTML = `<p class="hint">当前:<b>手动指定</b> → ${FX_KEY_LABEL[key] || key}</p>`;
    return;
  }
  // auto:算一下今天是什么节日
  const now = new Date(), m = now.getMonth() + 1, d = now.getDate();
  let today = '';
  if (m === 12 && d === 13) today = 'memorial';
  else if (m === 10 && d >= 1 && d <= 7) today = 'national-day';
  else if (m === 2 && d === 14) today = 'valentine';
  else if (m === 1 && d <= 2) today = 'new-year';
  else if (m === 12 && (d === 24 || d === 25)) today = 'christmas';
  else if (m === 5 && d >= 1 && d <= 5) today = 'labor';
  else if (m === 6 && d === 1) today = 'children';
  else if (m === 9 && d === 10) today = 'teacher';

  box.innerHTML = today
    ? `<p class="hint">当前:<b>按日期自动</b> → 今天正好是 ${FX_KEY_LABEL[today]}</p>`
    : '<p class="hint">当前:<b>按日期自动</b> → 今天不是节日,前台不显示特效。</p>';
}

/* ---------- 安全面板 ---------- */
async function loadSecOverview() {
  try {
    const d = await api('GET', '/api/security/overview');
    renderSecOverview(d);
  } catch (e) { toast('安全信息加载失败:' + e.message); }
}

function renderSecOverview(d) {
  const s = d.settings || {};

  // 顶部卡片
  const capOn = s.sec_captcha === '1';
  const c1 = document.getElementById('secCardCaptcha');
  document.getElementById('scCaptchaVal').textContent = capOn ? '已开启' : '未开启';
  c1.className = 'sec-card ' + (capOn ? 'ok' : 'bad');

  const f2 = document.getElementById('secCardFails');
  document.getElementById('scFailsVal').textContent = d.fails_24h + ' 次';
  f2.className = 'sec-card ' + (d.fails_24h === 0 ? 'ok' : d.fails_24h < 10 ? 'warn' : 'bad');

  const nb = (d.blocked || []).length;
  const c3 = document.getElementById('secCardBlocked');
  document.getElementById('scBlockedVal').textContent = nb + ' 个';
  c3.className = 'sec-card ' + (nb === 0 ? 'ok' : 'warn');

  const ns = (d.sessions || []).length;
  const c4 = document.getElementById('secCardSessions');
  document.getElementById('scSessionsVal').textContent = ns + ' 个';
  c4.className = 'sec-card ' + (ns <= 1 ? 'ok' : 'warn');

  // 表单回填
  document.getElementById('setCaptcha').checked = capOn;
  document.getElementById('setCaptchaLen').value = s.sec_captcha_len || 4;
  document.getElementById('setFailThreshold').value = s.sec_fail_threshold || 5;
  document.getElementById('setBlockMinutes').value = s.sec_block_minutes || 15;
  document.getElementById('setIdleMinutes').value = s.sec_idle_minutes ?? 60;
  document.getElementById('setSessionHours').value = s.sec_session_hours || 168;
  document.getElementById('setAuditKeep').value = s.sec_audit_keep || 500;

  // 封锁列表
  const bl = document.getElementById('secBlockedList');
  if (!nb) {
    bl.innerHTML = '<p class="hint">当前没有被封锁的 IP,很安全 ✨</p>';
  } else {
    const now = d.server_time || Math.floor(Date.now() / 1000);
    bl.innerHTML = `<table class="sec-table">
      <thead><tr><th>IP</th><th>剩余时间</th><th>失败次数</th><th>操作</th></tr></thead>
      <tbody>${d.blocked.map(b => {
        const left = Math.max(0, b.blocked_until - now);
        const mm = Math.floor(left / 60), ss = left % 60;
        return `<tr>
          <td>${esc(b.ip)}</td>
          <td>${mm} 分 ${String(ss).padStart(2,'0')} 秒</td>
          <td>${b.count}</td>
          <td><button class="mini-btn" onclick="unblockIp('${escAttr(b.ip)}')">解除</button></td>
        </tr>`;
      }).join('')}</tbody></table>`;
  }

  // 会话列表
  const sl = document.getElementById('secSessionList');
  if (!ns) {
    sl.innerHTML = '<p class="hint">没有活跃会话</p>';
  } else {
    const now = d.server_time || Math.floor(Date.now() / 1000);
    sl.innerHTML = `<table class="sec-table">
      <thead><tr><th>IP</th><th>设备</th><th>登录时间</th><th>最后活动</th><th>操作</th></tr></thead>
      <tbody>${d.sessions.map(x => {
        const c = new Date(x.created * 1000);
        const t = new Date(x.last_seen * 1000);
        const fmt = dt => `${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')} ` +
                          `${String(dt.getHours()).padStart(2,'0')}:${String(dt.getMinutes()).padStart(2,'0')}`;
        const ago = Math.floor((now - x.last_seen) / 60);
        const agoTxt = ago < 1 ? '刚刚' : ago < 60 ? `${ago} 分钟前` : `${Math.floor(ago/60)} 小时前`;
        return `<tr>
          <td>${esc(x.ip)}${x.current ? '<span class="cur-tag">当前</span>' : ''}</td>
          <td style="font-size:11.5px">${esc(x.ua || '未知')}</td>
          <td>${fmt(c)}</td>
          <td>${agoTxt}</td>
          <td>${x.current ? '—' :
            `<button class="mini-btn" onclick="revokeSession('${escAttr(x.sid)}')">踢下线</button>`}</td>
        </tr>`;
      }).join('')}</tbody></table>`;
  }
}

async function saveSecSettings() {
  const body = {
    sec_captcha: document.getElementById('setCaptcha').checked ? 1 : 0,
    sec_captcha_len: parseInt(document.getElementById('setCaptchaLen').value, 10),
    sec_fail_threshold: parseInt(document.getElementById('setFailThreshold').value, 10),
    sec_block_minutes: parseInt(document.getElementById('setBlockMinutes').value, 10),
    sec_idle_minutes: parseInt(document.getElementById('setIdleMinutes').value, 10),
    sec_session_hours: parseInt(document.getElementById('setSessionHours').value, 10),
    sec_audit_keep: parseInt(document.getElementById('setAuditKeep').value, 10),
  };
  // 前端先挡一次明显非法的值,省一次往返
  for (const [k, v] of Object.entries(body)) {
    if (Number.isNaN(v)) { toast(`${k} 要填数字`); return; }
  }
  try {
    await api('POST', '/api/security/settings', body);
    toast('安全设置已保存 ✅');
    loadSecOverview();
  } catch (e) { toast('保存失败:' + e.message); }
}

async function unblockIp(ip) {
  try {
    await api('POST', '/api/security/unblock', { ip });
    toast('已解除封锁:' + ip);
    loadSecOverview();
  } catch (e) { toast('操作失败:' + e.message); }
}

async function revokeSession(sid) {
  if (!confirm('确定把这个会话踢下线?对方需要重新登录。')) return;
  try {
    await api('POST', '/api/security/revoke', { sid });
    toast('已踢下线');
    loadSecOverview();
  } catch (e) { toast('操作失败:' + e.message); }
}

async function revokeAllSessions() {
  if (!confirm('踢掉除当前会话以外的所有登录?其他设备都需要重新登录。')) return;
  try {
    const r = await api('POST', '/api/security/revoke-all');
    toast(`已踢下线 ${r.revoked} 个会话`);
    loadSecOverview();
  } catch (e) { toast('操作失败:' + e.message); }
}

/* ---------- 审计日志 ---------- */
const ACTION_LABEL = {
  login_ok: '登录成功', login_fail: '登录失败', login_block: '触发封锁',
  login_blocked: '封锁期尝试', logout: '退出登录', pass_change: '改密码',
  sec_settings: '改安全设置', unblock: '解除封锁', revoke_session: '踢会话',
  revoke_all: '踢全部会话', audit_clear: '清空日志', session_idle: '空闲登出',
  upload: '上传图片', upload_del: '删除图片', import: '导入数据', export: '导出数据',
};
const ACTION_STYLE = {
  login_ok: 'act-ok', pass_change: 'act-ok', sec_settings: 'act-ok',
  login_fail: 'act-warn', login_block: 'act-bad', login_blocked: 'act-bad',
  audit_clear: 'act-bad', revoke_session: 'act-warn', revoke_all: 'act-warn',
};

async function loadAudit() {
  try {
    const keep = parseInt(document.getElementById('setAuditKeep')?.value || 100, 10);
    const d = await api('GET', '/api/security/audit?limit=' + Math.max(20, Math.min(keep || 100, 500)));
    const box = document.getElementById('secAuditList');
    if (!d.rows.length) {
      box.innerHTML = '<p class="hint">还没有审计记录</p>';
      return;
    }
    box.innerHTML = `<table class="sec-table">
      <thead><tr><th>时间</th><th>操作</th><th>IP</th><th>详情</th></tr></thead>
      <tbody>${d.rows.map(r => {
        const dt = new Date(r.ts * 1000);
        const t = `${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')} ` +
                  `${String(dt.getHours()).padStart(2,'0')}:${String(dt.getMinutes()).padStart(2,'0')}:` +
                  `${String(dt.getSeconds()).padStart(2,'0')}`;
        const lbl = ACTION_LABEL[r.action] || r.action;
        const cls = ACTION_STYLE[r.action] || '';
        return `<tr>
          <td style="white-space:nowrap">${t}</td>
          <td><span class="act-tag ${cls}">${esc(lbl)}</span></td>
          <td>${esc(r.ip || '—')}</td>
          <td style="font-size:11.5px">${esc(r.detail || '')}</td>
        </tr>`;
      }).join('')}</tbody></table>`;
  } catch (e) { toast('审计日志加载失败:' + e.message); }
}

async function clearAudit() {
  if (!confirm('清空所有审计日志?这个操作本身也会被记录。')) return;
  try {
    const r = await api('DELETE', '/api/security/audit');
    toast(`已清空 ${r.deleted} 条日志`);
    loadAudit();
  } catch (e) { toast('清空失败:' + e.message); }
}

// 按类型新增 profile 时预填 kind
function editProfileKind(kind) {
  editItem('profile', null, { kind });
}

/* ---------- 数据看板 ---------- */
let DASH_DAYS = 7;
let dashLoaded = false;

async function loadDashboard(days) {
  DASH_DAYS = days || DASH_DAYS;
  try {
    const j = await api('GET', `/api/stats/visits?days=${DASH_DAYS}`);
    renderDashboard(j);
    dashLoaded = true;
  } catch (e) {
    toast('看板加载失败:' + e.message);
  }
  // v1.10:新老访客 + 平均停留(独立接口,失败不挡主看板)
  try {
    const v = await api('GET', `/api/stats/visitors?days=${DASH_DAYS}`);
    const nb = document.getElementById('dc-newback');
    const du = document.getElementById('dc-dur');
    if (nb) nb.textContent = `${v.new ?? '–'} / ${v.back ?? '–'}`;
    if (du) du.textContent = v.avg_dur >= 60
      ? `${Math.floor(v.avg_dur / 60)}分${v.avg_dur % 60}秒` : `${v.avg_dur || 0}秒`;
  } catch (e) { /* 旧数据无 is_new 列时静默 */ }
}

function renderDashboard(d) {
  document.getElementById('dc-today').textContent = d.today;
  document.getElementById('dc-total').textContent = d.total_real;
  document.getElementById('dc-bots').textContent = d.total - d.total_real;

  const sum = d.by_day.reduce((a, b) => a + b.n, 0);
  document.getElementById('dc-range').textContent = sum;

  // ---- 趋势柱状图 ----
  const chart = document.getElementById('dashChart');
  if (!d.by_day.length) {
    chart.innerHTML = '<p class="hint" style="margin:auto">还没有数据,等有人来看看~</p>';
    document.getElementById('dashChartX')?.remove();
  } else {
    const max = Math.max(...d.by_day.map(x => x.n), 1);
    chart.innerHTML = d.by_day.map(x => {
      const h = Math.max(2, Math.round(x.n / max * 100));
      const mmdd = x.day.slice(5).replace('-', '/');
      return `<div class="bar-col ${x.n === 0 ? 'zero' : ''}">
        <span class="tip">${mmdd} · ${x.n} 次</span>
        <i style="height:${h}%"></i>
      </div>`;
    }).join('');
    // 首尾日期标注
    const first = d.by_day[0].day.slice(5).replace('-', '/');
    const last = d.by_day[d.by_day.length - 1].day.slice(5).replace('-', '/');
    let xa = document.getElementById('dashChartX');
    if (!xa) {
      xa = document.createElement('div');
      xa.className = 'chart-x';
      xa.id = 'dashChartX';
      chart.after(xa);
    }
    xa.innerHTML = `<span>${first}</span><span>${last}</span>`;
  }

  // ---- 来源 ----
  const refs = document.getElementById('dashRefs');
  if (!d.by_ref.length) {
    refs.innerHTML = '<p class="hint">还没有外部来源,基本都是直接访问</p>';
  } else {
    const rmax = Math.max(...d.by_ref.map(x => x.n), 1);
    refs.innerHTML = d.by_ref.map(x => `
      <div class="rank-row">
        <span class="rn">${esc(x.referer)}</span>
        <span class="rb"><i style="width:${Math.round(x.n / rmax * 100)}%"></i></span>
        <span class="rv">${x.n}</span>
      </div>`).join('');
  }

  // ---- 浏览器/系统 ----
  const uas = document.getElementById('dashUas');
  if (!d.by_ua.length) {
    uas.innerHTML = '<p class="hint">还没有数据</p>';
  } else {
    const umax = Math.max(...d.by_ua.map(x => x.n), 1);
    uas.innerHTML = d.by_ua.map(x => `
      <div class="rank-row">
        <span class="rn">${esc(x.ua)}</span>
        <span class="rb"><i style="width:${Math.round(x.n / umax * 100)}%"></i></span>
        <span class="rv">${x.n}</span>
      </div>`).join('');
  }

  // ---- 24 小时 ----
  const hours = document.getElementById('dashHours');
  const hmax = Math.max(...d.by_hour, 1);
  hours.innerHTML = d.by_hour.map((n, h) => {
    const pct = Math.round(n / hmax * 100);
    return `<div class="h ${pct > 60 ? 'hot' : ''}"
      style="height:${Math.max(6, pct)}%"
      data-tip="${h}:00 · ${n} 次"></div>`;
  }).join('');
  let hx = document.getElementById('dashHoursX');
  if (!hx) {
    hx = document.createElement('div');
    hx.className = 'hours-x';
    hx.id = 'dashHoursX';
    hours.after(hx);
  }
  hx.innerHTML = '<span>0:00</span><span>6:00</span><span>12:00</span><span>18:00</span><span>23:00</span>';

  // ---- 访客城市 ----
  const cities = document.getElementById('dashCities');
  if (!d.cities || !d.cities.length) {
    cities.innerHTML = '<p class="hint">还没有城市数据(新访客进来后自动解析,稍等一会儿)</p>';
  } else {
    const cmax = Math.max(...d.cities.map(x => x.count), 1);
    cities.innerHTML = d.cities.map(x => `
      <div class="rank-row">
        <span class="rn">📍 ${esc(x.city)}</span>
        <span class="rb"><i style="width:${Math.round(x.count / cmax * 100)}%"></i></span>
        <span class="rv">${x.count} 次</span>
      </div>`).join('');
  }

  // ---- 最近访问 ----
  const recent = document.getElementById('dashRecent');
  if (!d.recent.length) {
    recent.innerHTML = '<p class="hint">还没有访问记录</p>';
  } else {
    recent.innerHTML = `<table class="recent-table">
      <thead><tr><th>时间</th><th>路径</th><th>来源</th><th>设备</th></tr></thead>
      <tbody>${d.recent.map(r => {
        const dt = new Date(r.ts * 1000);
        const t = `${String(dt.getMonth()+1).padStart(2,'0')}-${String(dt.getDate()).padStart(2,'0')} ` +
                  `${String(dt.getHours()).padStart(2,'0')}:${String(dt.getMinutes()).padStart(2,'0')}`;
        return `<tr>
          <td>${t}</td>
          <td>${esc(r.path)}</td>
          <td>${r.referer ? esc(r.referer) : '<span style="color:#8a8494">直接访问</span>'}</td>
          <td>${esc(r.ua)}</td>
        </tr>`;
      }).join('')}</tbody></table>`;
  }
}

// 区间切换
document.querySelectorAll('.rbtn').forEach(b => {
  b.addEventListener('click', () => {
    document.querySelectorAll('.rbtn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    loadDashboard(parseInt(b.dataset.days, 10));
  });
});

function renderSkills() {
  const box = document.getElementById('list-skills');
  box.innerHTML = DATA.skills.map(s => `
    <div class="item">
      <div class="item-top">
        <span class="badge ${s.category}">${CATS[s.category] || s.category}</span>
        <span class="meta">#${s.sort}</span>
      </div>
      <h3>${esc(s.name)}</h3>
      <div class="meta">${s.percent}%</div>
      <div class="bar-mini"><i class="bf-${escAttr(s.color || 'teal')}" style="width:${s.percent}%"></i></div>
      ${s.note ? `<div class="note">${esc(s.note)}</div>` : ''}
      <div class="ops">
        <button class="op edit" onclick="editItem('skills', ${s.id})">✏️ 编辑</button>
        <button class="op del" onclick="delItem('skills', ${s.id})">🗑️ 删除</button>
      </div>
    </div>`).join('') || '<p class="hint">还没有技能,点上面的「新增技能」加一个吧~</p>';
}

function renderTimeline() {
  const box = document.getElementById('list-timeline');
  box.innerHTML = DATA.timeline.map(e => `
    <div class="item">
      <div class="item-top">
        <span class="badge serious">${esc(e.emoji)} ${esc(e.time_label)}</span>
        <span class="meta">#${e.sort}</span>
      </div>
      <h3>${esc(e.title)}</h3>
      ${e.content ? `<div class="note">${esc(e.content)}</div>` : ''}
      <div class="ops">
        <button class="op edit" onclick="editItem('timeline', ${e.id})">✏️ 编辑</button>
        <button class="op del" onclick="delItem('timeline', ${e.id})">🗑️ 删除</button>
      </div>
    </div>`).join('') || '<p class="hint">时间线还是空的,记录一件校园大事吧~</p>';
}

function renderStats() {
  const box = document.getElementById('list-stats');
  box.innerHTML = DATA.stats.map(s => `
    <div class="item">
      <div class="item-top">
        <span class="badge passive">${esc(s.emoji)} ${esc(s.number)}${esc(s.unit)}</span>
        <span class="meta">#${s.sort}</span>
      </div>
      <h3>${esc(s.label)}</h3>
      <div class="ops">
        <button class="op edit" onclick="editItem('stats', ${s.id})">✏️ 编辑</button>
        <button class="op del" onclick="delItem('stats', ${s.id})">🗑️ 删除</button>
      </div>
    </div>`).join('') || '<p class="hint">还没有趣味数据,来一个?~</p>';
}

function renderWorks() {
  const box = document.getElementById('list-works');
  box.innerHTML = DATA.works.map(w => `
    <div class="item">
      <div class="item-top">
        <span class="badge serious">${esc(w.emoji)} ${esc(w.pill)}</span>
        <span class="meta">#${w.sort}</span>
      </div>
      <h3>${esc(w.title)}</h3>
      ${w.desc ? `<div class="note">${esc(w.desc)}</div>` : ''}
      ${w.link ? `<div class="note">🔗 ${esc(w.link)}</div>` : '<div class="note">(无链接)</div>'}
      <div class="ops">
        <button class="op edit" onclick="editItem('works', ${w.id})">✏️ 编辑</button>
        <button class="op del" onclick="delItem('works', ${w.id})">🗑️ 删除</button>
      </div>
    </div>`).join('') || '<p class="hint">项目墙空空的,加个项目吧~</p>';
}

function renderProfile() {
  const KIND = { about:'自我介绍', info:'信息卡片' };
  const make = p => `
    <div class="item">
      <div class="item-top">
        <span class="badge ${p.kind === 'about' ? 'serious' : 'passive'}">${esc(p.emoji)} ${KIND[p.kind] || p.kind}</span>
        <span class="meta">#${p.sort}</span>
      </div>
      <h3>${esc(p.label)}</h3>
      ${p.value ? `<div class="note">${esc(p.value)}</div>` : ''}
      <div class="ops">
        <button class="op edit" onclick="editItem('profile', ${p.id})">✏️ 编辑</button>
        <button class="op del" onclick="delItem('profile', ${p.id})">🗑️ 删除</button>
      </div>
    </div>`;

  const abouts = DATA.profile.filter(p => p.kind === 'about');
  const infos = DATA.profile.filter(p => p.kind === 'info');

  document.getElementById('list-profile-about').innerHTML =
    abouts.map(make).join('') || '<p class="hint">还没有自我介绍段落~</p>';
  document.getElementById('list-profile-info').innerHTML =
    infos.map(make).join('') || '<p class="hint">还没有信息卡片~</p>';
}

/* ---------- 编辑 / 新增 ---------- */
const FIELDS = {
  skills: [
    { k:'name',    label:'技能名(可带 emoji)', type:'text' },
    { k:'percent', label:'熟练度 %',           type:'number', min:0, max:100 },
    { k:'note',    label:'吐槽小字',           type:'text' },
    { k:'category',label:'分类',               type:'select', opts:CATS },
    { k:'color',   label:'进度条颜色',          type:'select',
      opts:{teal:'薄荷绿', pink:'粉', yellow:'黄', purple:'紫', orange:'橙', blue:'蓝'} },
    { k:'sort',    label:'排序(小的在前)',     type:'number' },
  ],
  timeline: [
    { k:'emoji',      label:'图标 emoji',      type:'text' },
    { k:'time_label', label:'时间(如 2026.09 / 现在)', type:'text' },
    { k:'title',      label:'标题',            type:'text' },
    { k:'content',    label:'内容描述',        type:'textarea' },
    { k:'sort',       label:'排序(小的在前)',  type:'number' },
  ],
  stats: [
    { k:'emoji',  label:'图标 emoji',       type:'text' },
    { k:'number', label:'数字',             type:'number' },
    { k:'unit',   label:'单位(如 杯 / 次)', type:'text' },
    { k:'label',  label:'说明文字',          type:'text' },
    { k:'sort',   label:'排序(小的在前)',   type:'number' },
  ],
  works: [
    { k:'emoji', label:'封面 emoji',        type:'text' },
    { k:'cover', label:'封面底色',           type:'select',
      opts:{pink:'粉', yellow:'黄', teal:'薄荷绿', purple:'紫', orange:'橙', blue:'蓝'} },
    { k:'title', label:'项目名',             type:'text' },
    { k:'desc',  label:'项目描述',           type:'textarea' },
    { k:'pill',  label:'状态标签(如 进行中)', type:'text' },
    { k:'link',  label:'链接(留空则不显示)', type:'text' },
    { k:'sort',  label:'排序(小的在前)',     type:'number' },
  ],
  profile: [
    { k:'kind',  label:'类型',               type:'select',
      opts:{about:'自我介绍段落', info:'信息卡片'} },
    { k:'emoji', label:'图标 emoji(信息卡片用)', type:'text' },
    { k:'label', label:'小标题 / 卡片标题',   type:'text' },
    { k:'value', label:'正文 / 卡片内容',     type:'textarea' },
    { k:'sort',  label:'排序(小的在前)',     type:'number' },
  ],
};

function editItem(kind, id, preset) {
  const list = DATA[kind];
  const item = id ? list.find(x => x.id === id) : null;
  const fields = FIELDS[kind];

  // profile 拆成两个面板,按 kind 找到对应的列表容器
  const targetKind = item ? item.kind : (preset && preset.kind);
  const listId = kind === 'profile'
    ? (targetKind === 'about' ? 'list-profile-about' : 'list-profile-info')
    : 'list-' + kind;

  const box = item
    ? event.target.closest('.item')
    : document.getElementById(listId);

  const form = document.createElement('div');
  form.className = 'item';
  form.style.borderColor = 'var(--teal)';
  form.innerHTML = fields.map(f => {
    const v = item ? (item[f.k] ?? '') : (preset && preset[f.k] !== undefined ? preset[f.k] : '');
    if (f.type === 'select') {
      return `<div class="ef"><label>${f.label}</label><select data-k="${f.k}">${
        Object.entries(f.opts).map(([val, txt]) =>
          `<option value="${val}" ${v === val ? 'selected' : ''}>${txt}</option>`).join('')
      }</select></div>`;
    }
    if (f.type === 'textarea') {
      return `<div class="ef"><label>${f.label}</label><textarea data-k="${f.k}">${esc(v)}</textarea></div>`;
    }
    return `<div class="ef"><label>${f.label}</label>
      <input data-k="${f.k}" type="${f.type}" ${f.min !== undefined ? `min="${f.min}" max="${f.max}"` : ''} value="${escAttr(v)}" /></div>`;
  }).join('') + `
    <div class="ops">
      <button class="op save" id="btn-save">💾 保存</button>
      <button class="op cancel" id="btn-cancel">取消</button>
    </div>`;

  // 新增:表单插到列表最前面;编辑:替换原卡片
  if (item) { box.replaceWith(form); } else { box.prepend(form); }
  const first = form.querySelector('input, select, textarea');
  if (first) first.focus();

  form.querySelector('#btn-cancel').onclick = () => renderAll();
  form.querySelector('#btn-save').onclick = async () => {
    const body = {};
    form.querySelectorAll('[data-k]').forEach(el => {
      body[el.dataset.k] = el.type === 'number' ? parseInt(el.value || '0', 10) : el.value.trim();
    });
    try {
      if (item) {
        await api('PUT', `/api/${kind}/${id}`, body);
        Object.assign(item, body);
        toast('保存成功 ✅');
      } else {
        const row = await api('POST', `/api/${kind}`, body);
        list.push(row);
        toast('新增成功 🎉');
      }
      renderAll();
    } catch (e) { toast('出错了:' + e.message + ' 😵'); }
  };
}

async function delItem(kind, id) {
  const list = DATA[kind];
  const item = list.find(x => x.id === id);
  const name = item ? (item.name || item.title || item.label) : '';
  if (!confirm(`确定删除「${name}」吗?删了就没了哦!`)) return;
  try {
    await api('DELETE', `/api/${kind}/${id}`);
    DATA[kind] = list.filter(x => x.id !== id);
    toast('已删除 🗑️');
    renderAll();
  } catch (e) { toast('出错了:' + e.message + ' 😵'); }
}

renderAll();

/* ---------- 图片上传 ---------- */
const fileInput = document.getElementById('fileInput');
const uploadZone = document.getElementById('uploadZone');

async function uploadFile(file) {
  if (!file) return;
  if (file.size > 5 * 1024 * 1024) { toast('图片太大了,压缩到 5MB 以内 😵'); return; }
  const fd = new FormData();
  fd.append('file', file);
  toast('上传中...');
  try {
    const res = await fetch('/api/upload', { method: 'POST', body: fd });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) { toast('上传失败:' + (j.error || res.status) + ' 😵'); return; }
    toast('上传成功 🎉');
    loadUploads();
  } catch (e) { toast('网络出错了,再试试 😵'); }
}

fileInput.addEventListener('change', e => {
  uploadFile(e.target.files[0]);
  e.target.value = '';
});

// 拖拽上传
['dragenter', 'dragover'].forEach(ev =>
  uploadZone.addEventListener(ev, e => { e.preventDefault(); uploadZone.classList.add('dragover'); }));
['dragleave', 'drop'].forEach(ev =>
  uploadZone.addEventListener(ev, e => { e.preventDefault(); uploadZone.classList.remove('dragover'); }));
uploadZone.addEventListener('drop', e => {
  const f = e.dataTransfer.files && e.dataTransfer.files[0];
  uploadFile(f);
});

async function loadUploads() {
  const box = document.getElementById('upGrid');
  try {
    const res = await fetch('/api/uploads');
    if (!res.ok) return;
    const { items } = await res.json();
    box.innerHTML = items.map(it => `
      <div class="up-item">
        <img src="${escAttr(it.url)}" alt="" loading="lazy" />
        <div class="up-meta">${(it.size / 1024).toFixed(0)} KB · ${esc(it.mtime)}</div>
        <div class="up-ops">
          <button class="copy" onclick="copyUrl('${escAttr(it.url)}')">📋 复制路径</button>
          <button class="rm" onclick="delUpload('${escAttr(it.name)}')">🗑️</button>
        </div>
      </div>`).join('') || '<p class="hint">还没传过图,拖一张进来试试~</p>';
  } catch {}
}

function copyUrl(url) {
  navigator.clipboard.writeText(url).then(
    () => toast('路径已复制:' + url),
    () => toast('复制失败,手动选中吧:' + url)
  );
}

async function delUpload(name) {
  if (!confirm('删除这张图?如果页面正在用会变成裂图哦')) return;
  try {
    const res = await fetch('/api/uploads/' + encodeURIComponent(name), { method: 'DELETE' });
    if (!res.ok) { toast('删除失败 😵'); return; }
    toast('已删除 🗑️');
    loadUploads();
  } catch { toast('网络出错了 😵'); }
}
loadUploads();

/* ---------- 数据导入 ---------- */
const importInput = document.getElementById('importInput');
let pendingReplace = false;

importInput.addEventListener('change', e => {
  const f = e.target.files[0];
  e.target.value = '';
  const replace = pendingReplace;
  pendingReplace = false;
  if (f) doImport(f, replace);
});

function importReplace() {
  if (!confirm('⚠️ 会先清空所有内容再导入,确定吗?')) return;
  pendingReplace = true;
  document.getElementById('importInput').click();
}

async function doImport(file, replace) {
  if (!confirm(replace ? '⚠️ 确定清空并恢复?' : '确定用这个文件恢复内容吗?')) return;
  try {
    const text = await file.text();
    const payload = JSON.parse(text);
    payload.replace = replace;
    const res = await fetch('/api/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) { toast('恢复失败:' + (j.error || res.status) + ' 😵'); return; }
    const summary = Object.entries(j.counts || {}).map(([k, v]) => `${k}:${v}`).join(' ');
    toast('恢复成功 ✅ ' + summary);
    setTimeout(() => location.reload(), 1200);
  } catch (err) {
    toast('文件读取失败,确认是导出的 JSON 吗? 😵');
  }
}

/* ---------- 改密码 ---------- */
const MUST_CHANGE = !!window.__ADMIN_MUST_CHANGE__;
const passModal = document.getElementById('passModal');

function openPassModal() {
  document.getElementById('passErr').style.display = 'none';
  document.getElementById('passSub').textContent = MUST_CHANGE
    ? '检测到初始密码 admin,必须马上改一个!' : '改完要用新密码重新登录哦';
  passModal.classList.add('open');
  setTimeout(() => document.getElementById('oldPass').focus(), 50);
}
function closePassModal() { passModal.classList.remove('open'); }

async function submitPassword() {
  const err = document.getElementById('passErr');
  const old1 = document.getElementById('oldPass').value;
  const new1 = document.getElementById('newPass').value;
  const new2 = document.getElementById('newPass2').value;
  err.style.display = 'none';

  if (new1 !== new2) { showPerr('两次输入的新密码不一样'); return; }
  if (new1.length < 6) { showPerr('新密码至少 6 位啦'); return; }
  if (new1 === 'admin') { showPerr('不能还用 admin 当密码!换一个'); return; }

  try {
    const res = await fetch('/api/password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ old: old1, new: new1 })
    });
    const j = await res.json().catch(() => ({}));
    if (!res.ok) { showPerr(j.error || '出错了,再试试'); return; }
    alert('密码改好啦!现在用新密码重新登录一次 ✅');
    location.href = '/admin/login';
  } catch { showPerr('网络出问题了,再试试'); }
}

function showPerr(msg) {
  const err = document.getElementById('passErr');
  err.textContent = msg;
  err.style.display = 'block';
}

passModal.addEventListener('click', e => { if (e.target === passModal) closePassModal(); });
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') { closePassModal(); closeSidebar(); }
});

/* ---------- 初始化 ---------- */
renderAll();
restoreGroups();

/* ==================== v1.9.0:留言板管理 ==================== */

const MSG_STATE = { 0: '待审核', 1: '展示中', 2: '已隐藏' };
const MSG_STATE_CLS = { 0: 'warn', 1: 'ok', 2: 'muted' };

function fmtMsgTime(ts) {
  const d = new Date(ts * 1000);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getMonth() + 1}-${d.getDate()} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

async function loadMessages() {
  try {
    const r = await fetch('/api/messages/admin');
    if (r.status === 401) { location.href = '/admin/login'; return; }
    const d = await r.json();
    const c = d.counts || {};
    document.getElementById('msgPending').textContent = c.pending ?? 0;
    document.getElementById('msgShownN').textContent = c.shown ?? 0;
    document.getElementById('msgTotalN').textContent = c.total ?? 0;
    const cnt = document.getElementById('cnt-messages');
    if (cnt) cnt.textContent = c.pending ? `待审${c.pending}` : c.total;

    const list = document.getElementById('msgAdminList');
    if (!d.messages.length) {
      list.innerHTML = '<p class="hint">还没有留言,去前台发一条试试~</p>';
      return;
    }
    list.innerHTML = d.messages.map(m => `
      <div class="msg-admin-item" data-id="${m.id}">
        <div class="mai-head">
          <b>${esc(m.name)}</b>
          <span class="badge ${MSG_STATE_CLS[m.shown]}">${MSG_STATE[m.shown]}</span>
          <span class="hint">${fmtMsgTime(m.ts)} · ${esc(m.ip || '未知IP')} · ${m.color}</span>
        </div>
        <div class="mai-body">${esc(m.body)}</div>
        ${m.reply ? `<div class="mai-reply">站主回复:${esc(m.reply)}</div>` : ''}
        <div class="ops" style="margin-top:8px">
          ${m.shown !== 1 ? `<button class="op save" onclick="msgMod(${m.id},'show')">✅ 展示</button>` : ''}
          ${m.shown === 1 ? `<button class="op" onclick="msgMod(${m.id},'hide')">🙈 隐藏</button>` : ''}
          ${m.shown === 2 ? `<button class="op" onclick="msgMod(${m.id},'pending')">↩️ 转待审</button>` : ''}
          <button class="op edit" onclick="msgReply(${m.id},'${esc(m.reply || '').replace(/'/g, "\\'")}')">💬 回复</button>
          <button class="op del" onclick="msgDel(${m.id})">🗑️ 删除</button>
        </div>
      </div>`).join('');
  } catch (e) {
    console.error('loadMessages', e);
  }
}

async function msgMod(id, action) {
  const r = await fetch(`/api/messages/${id}/mod`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action })
  });
  const d = await r.json();
  if (!d.ok) return alert(d.error || '操作失败');
  loadMessages();
}

function msgReply(id, current) {
  const reply = prompt('输入站主回复(留空清除回复,最多 140 字):', current || '');
  if (reply === null) return;
  fetch(`/api/messages/${id}/mod`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'reply', reply })
  }).then(r => r.json()).then(d => {
    if (!d.ok) return alert(d.error || '回复失败');
    loadMessages();
  });
}

async function msgDel(id) {
  if (!confirm('确定删除这条留言?删了就找不回来了')) return;
  const r = await fetch(`/api/messages/${id}/mod`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'delete' })
  });
  const d = await r.json();
  if (!d.ok) return alert(d.error || '删除失败');
  loadMessages();
}

/* ==================== v1.9.0:点赞统计 ==================== */

const PAGE_NAMES = {
  home: '🏠 首页', about: '🧍 关于我', skills: '🎯 技能树',
  works: '🛠️ 项目墙', campus: '🗺️ 校园日常', map: '📍 来访地图', contact: '📬 来找我玩',
};

async function loadLikes() {
  try {
    const r = await fetch('/api/likes/admin');
    if (r.status === 401) { location.href = '/admin/login'; return; }
    const d = await r.json();
    document.getElementById('likeTotal').textContent = d.total || 0;

    const entries = Object.entries(d.likes || {}).sort((a, b) => b[1] - a[1]);
    document.getElementById('likeBest').textContent =
      entries.length && entries[0][1] > 0
        ? (PAGE_NAMES[entries[0][0]] || entries[0][0]).split(' ').pop()
        : '–';

    const max = Math.max(1, ...entries.map(e => e[1]));
    document.getElementById('likeBars').innerHTML = entries.map(([page, n]) => `
      <div class="like-row">
        <span class="like-page">${PAGE_NAMES[page] || page}</span>
        <div class="like-bar-track"><div class="like-bar-fill" style="width:${Math.round(n / max * 100)}%"></div></div>
        <b class="like-n-num">${n}</b>
      </div>`).join('');
  } catch (e) {
    console.error('loadLikes', e);
  }
}

/* ==================== v1.10:站点公告管理 ==================== */

async function loadNotices() {
  try {
    const r = await api('GET', '/api/notices/admin');
    const list = document.getElementById('noticeAdminList');
    if (!r.notices || !r.notices.length) {
      list.innerHTML = '<p class="hint">还没有公告,发一条试试~</p>';
      return;
    }
    list.innerHTML = r.notices.map(n => `
      <div class="msg-admin-item">
        <div class="mai-head">
          <span class="badge ${n.active ? 'ok' : 'muted'}">${n.active ? '展示中' : '已下架'}</span>
          <span class="hint">${fmtMsgTime(n.ts)}</span>
        </div>
        <div class="mai-body">${esc(n.body)}</div>
        <div class="ops" style="margin-top:8px">
          ${n.active
            ? `<button class="op" onclick="noticeMod(${n.id},'off')">⬇️ 下架</button>`
            : `<button class="op save" onclick="noticeMod(${n.id},'on')">⬆️ 上架</button>`}
          <button class="op del" onclick="noticeDel(${n.id})">🗑️ 删除</button>
        </div>
      </div>`).join('');
  } catch (e) { console.error('loadNotices', e); }
}

async function noticeMod(id, action) {
  try {
    await api('POST', `/api/notices/${id}/mod`, { action });
    loadNotices();
  } catch (e) { toast('操作失败:' + e.message); }
}

async function noticeDel(id) {
  if (!confirm('删除这条公告?')) return;
  try {
    await api('POST', `/api/notices/${id}/mod`, { action: 'delete' });
    loadNotices();
  } catch (e) { toast('删除失败:' + e.message); }
}

(function initNoticeForm() {
  const input = document.getElementById('noticeInput');
  const btn = document.getElementById('noticeSend');
  if (!input || !btn) return;
  async function send() {
    const body = input.value.trim();
    if (!body) return toast('先写公告内容~');
    try {
      await api('POST', '/api/notices/admin', { body });
      input.value = '';
      loadNotices();
    } catch (e) { toast('发布失败:' + e.message); }
  }
  btn.addEventListener('click', send);
  input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
})();

/* ==================== v1.10:倒计时管理 ==================== */

function fmtCdTarget(target) {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(target || '');
  if (!m) return target;
  const diff = Math.ceil((new Date(+m[1], +m[2] - 1, +m[3]) - new Date()) / 86400000);
  if (diff > 0) return `${target}(还有 ${diff} 天)`;
  if (diff === 0) return `${target}(就是今天!)`;
  return `${target}(过去 ${-diff + 1} 天)`;
}

async function loadCountdowns() {
  try {
    const r = await api('GET', '/api/countdowns/admin');
    const list = document.getElementById('cdAdminList');
    if (!r.countdowns || !r.countdowns.length) {
      list.innerHTML = '<p class="hint">还没有倒计时,加一个吧(考试/比赛/纪念日)</p>';
      return;
    }
    list.innerHTML = r.countdowns.map(c => `
      <div class="msg-admin-item">
        <div class="mai-head">
          <b>${c.emoji || '⏳'} ${esc(c.title)}</b>
          <span class="badge ${c.active ? 'ok' : 'muted'}">${c.active ? '启用' : '停用'}</span>
          <span class="hint">${fmtCdTarget(c.target)}</span>
        </div>
        <div class="ops" style="margin-top:8px">
          <button class="op edit" onclick='cdEdit(${JSON.stringify(
    { id: c.id, title: c.title, target: c.target, emoji: c.emoji, active: !!c.active }
  ).replace(/'/g, '&#39;')})'>✏️ 编辑</button>
          <button class="op del" onclick="cdDel(${c.id})">🗑️ 删除</button>
        </div>
      </div>`).join('');
  } catch (e) { console.error('loadCountdowns', e); }
}

function cdEdit(c) {
  document.getElementById('cdTitle').value = c.title;
  document.getElementById('cdTarget').value = c.target;
  document.getElementById('cdEmoji').value = c.emoji || '';
  document.getElementById('cdActive').checked = !!c.active;
  document.getElementById('cdSave').dataset.id = c.id;
  toast('已载入编辑区,改完点保存');
}

async function cdDel(id) {
  if (!confirm('删除这个倒计时?')) return;
  try {
    await api('POST', `/api/countdowns/${id}/delete`);
    loadCountdowns();
  } catch (e) { toast('删除失败:' + e.message); }
}

(function initCdForm() {
  const btn = document.getElementById('cdSave');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const payload = {
      id: btn.dataset.id ? Number(btn.dataset.id) : null,
      title: document.getElementById('cdTitle').value,
      target: document.getElementById('cdTarget').value,
      emoji: document.getElementById('cdEmoji').value || '⏳',
      active: document.getElementById('cdActive').checked,
    };
    try {
      await api('POST', '/api/countdowns/admin', payload);
      delete btn.dataset.id;
      document.getElementById('cdTitle').value = '';
      document.getElementById('cdTarget').value = '';
      document.getElementById('cdEmoji').value = '';
      document.getElementById('cdActive').checked = true;
      loadCountdowns();
    } catch (e) { toast('保存失败:' + e.message); }
  });
})();

// 前台特效:模式/开关变化时联动「指定节日」是否可点
(function initFxEvents() {
  const modeEl = document.getElementById('fxMode');
  const onEl = document.getElementById('fxHolidayOn');
  if (modeEl) modeEl.addEventListener('change', updateFxKeyDisabled);
  if (onEl) onEl.addEventListener('change', updateFxKeyDisabled);
})();

// 恢复上次看的面板;没有就用 URL hash;再没有就技能树
(function initPanel() {
  let name = location.hash.replace('#', '');
  if (!PANELS[name]) {
    try { name = localStorage.getItem('admin_panel') || 'skills'; } catch (e) { name = 'skills'; }
  }
  showPanel(name);
})();

// 初始密码未改 → 自动弹窗提醒
if (MUST_CHANGE) setTimeout(openPassModal, 400);
