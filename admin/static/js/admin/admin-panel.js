/* ============================================================
   后台 · admin-panel:侧边栏导航 + 面板切换 + 前台特效 +
   安全面板(总览/设置/封锁/会话/审计)+ 数据看板(v2.1 拆分)
   ============================================================ *//* ---------- 侧边栏导航 ---------- */
const PANELS = {
  'skills':        { title:'🎯 技能树管理',    crumb:'内容管理 / 技能树' },
  'timeline':      { title:'🗺️ 校园日常管理',  crumb:'内容管理 / 校园日常' },
  'stats':         { title:'🧮 趣味统计管理',  crumb:'内容管理 / 趣味统计' },
  'works':         { title:'🛠️ 项目墙管理',    crumb:'内容管理 / 项目墙' },
  'honors':        { title:'🏆 荣誉墙管理',    crumb:'内容管理 / 荣誉墙' },
  'notes':         { title:'📝 随手记管理',    crumb:'内容管理 / 随手记' },
  'friendlinks':   { title:'🔗 友情链接管理',  crumb:'内容管理 / 友情链接' },
  'songs':         { title:'🎵 音乐管理',      crumb:'内容管理 / 音乐' },
  'messages':      { title:'✉️ 留言板',        crumb:'内容管理 / 留言板' },
  'profile-about': { title:'✍️ 自我介绍段落',  crumb:'个人信息 / 自我介绍' },
  'profile-info':  { title:'🪪 信息卡片',      crumb:'个人信息 / 信息卡片' },
  'site-info':     { title:'🏷️ 站点信息',      crumb:'个人信息 / 站点信息' },
  'uploads':       { title:'🖼️ 图片库',        crumb:'媒体资源 / 图片库' },
  'gallery':       { title:'📷 相册',          crumb:'媒体资源 / 相册' },
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

/* ---------- v2.5 站点信息 ----------
   姓名/站名/学校/专业/年级/方向/标语/版权后缀/建站年份
   全部存后台 settings 表,前台 7 个页面动态套用。
   面板里用 input 逐项编辑,保存走 PUT /api/site。 */
let SITE_VALUES = {};
let SITE_FIELDS = [];

function renderSiteForm() {
  const data = (DATA && DATA.site) || {};
  const fields = (DATA && DATA.site_fields) || [];
  SITE_VALUES = { ...data };
  SITE_FIELDS = fields;

  const box = document.getElementById('siteForm');
  if (!box) return;
  if (!fields.length) {
    box.innerHTML = '<p class="hint">没拿到字段定义,请刷新页面</p>';
    return;
  }
  box.innerHTML = fields.map(f => `
    <div class="sf-row">
      <label class="sf-label">
        ${esc(f.label)}
        <span class="sf-note">默认:${esc(f.default)}</span>
      </label>
      <input class="sf-input" id="site-${f.key}" data-key="${f.key}"
             value="${escAttr(SITE_VALUES[f.key] || f.default)}"
             placeholder="${escAttr(f.default)}"
             oninput="onSiteInput()" />
    </div>`).join('');
  updateSitePreview();
}

function onSiteInput() {
  SITE_FIELDS.forEach(f => {
    const el = document.getElementById('site-' + f.key);
    if (el) SITE_VALUES[f.key] = el.value;
  });
  updateSitePreview();
}

function updateSitePreview() {
  const pv = document.getElementById('sitePreview');
  if (!pv) return;
  const v = SITE_VALUES;
  const year = new Date().getFullYear();
  pv.innerHTML = `
    <div>🌐 浏览器标签:<b>${esc(v.site_owner)} · 大学生活实录 🎓</b></div>
    <div>🧭 导航栏 logo:<b>${esc(v.site_name)}</b></div>
    <div>🎓 首屏徽章:<b>${esc(v.site_school)} · ${esc(v.site_major)} · ${esc(v.site_grade)}</b></div>
    <div>👋 首屏标题:<b>嗨,我是 ${esc(v.site_owner)} 👋</b></div>
    <div>🏷️ 身份标签:<b>${esc(v.site_focus)}</b></div>
    <div>📝 页脚版权:<b>© ${esc(v.site_start_year || year)} ${esc(v.site_owner)} · ${esc(v.site_school)} · ${esc(v.site_credit)} · ${esc(v.site_slogan)}</b></div>`;
}

async function saveSiteInfo() {
  onSiteInput();
  const hint = document.getElementById('siteSavedHint');
  try {
    const r = await api('PUT', '/api/site', SITE_VALUES);
    SITE_VALUES = { ...r.values };
    if (DATA) DATA.site = r.values;
    renderSiteForm();
    if (hint) hint.textContent = '✅ 已保存,前台刷新后生效';
    toast('站点信息已保存');
  } catch (e) {
    if (hint) hint.textContent = '❌ 保存失败:' + e.message;
    toast('保存失败:' + e.message);
  }
  setTimeout(() => { if (hint) hint.textContent = ''; }, 4000);
}

function resetSiteInfo() {
  if (!confirm('把所有站点信息恢复成默认值?')) return;
  const def = {};
  SITE_FIELDS.forEach(f => { def[f.key] = f.default; });
  SITE_VALUES = def;
  renderSiteForm();
  toast('已填入默认值,点保存后生效');
}

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
  if (name === 'gallery' && typeof loadGallery === 'function') loadGallery();

  // v2.5 站点信息:进面板时用当前值填表
  if (name === 'site-info') renderSiteForm();

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
  // v2.2 新内容类型
  set('cnt-honors', (DATA.honors || []).length);
  set('cnt-notes', (DATA.notes || []).length);
  set('cnt-friendlinks', (DATA.friendlinks || []).length);
  // v2.4 音乐
  set('cnt-songs', (DATA.songs || []).length);
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
  // v2.3 密码策略/失败时延/IP 绑定
  document.getElementById('setPassMinlen').value = s.sec_pass_minlen || 8;
  document.getElementById('setPassClasses').value = s.sec_pass_classes || 2;
  document.getElementById('setLoginDelay').value = s.sec_login_delay ?? 1;
  document.getElementById('setBindIp').checked = s.sec_bind_ip === '1';

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
    // v2.3 密码策略/失败时延/IP 绑定
    sec_pass_minlen: parseInt(document.getElementById('setPassMinlen').value, 10),
    sec_pass_classes: parseInt(document.getElementById('setPassClasses').value, 10),
    sec_login_delay: parseInt(document.getElementById('setLoginDelay').value, 10),
    sec_bind_ip: document.getElementById('setBindIp').checked ? 1 : 0,
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
    toast('已放行:' + ip);
    loadSecOverview();
  } catch (e) { toast('操作失败:' + e.message); }
}

async function revokeSession(sid) {
  if (!confirm('确定把这个会话踢下线?对方需要重新登录。')) return;
  try {
    await api('POST', '/api/security/revoke', { sid });
    toast('已让它退出登录');
    loadSecOverview();
  } catch (e) { toast('操作失败:' + e.message); }
}

async function revokeAllSessions() {
  if (!confirm('踢掉除当前会话以外的所有登录?其他设备都需要重新登录。')) return;
  try {
    const r = await api('POST', '/api/security/revoke-all');
    toast(`已让它退出登录 ${r.revoked} 个会话`);
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
  } catch (e) { toast('操作记录加载失败:' + e.message); }
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
