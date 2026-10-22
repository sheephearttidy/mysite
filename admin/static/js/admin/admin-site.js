/* ============================================================
   后台 · admin-site:站点运营(公告/倒计时)+ 面板记忆初始化
   (v2.1 拆分)
   ============================================================ *//* ==================== v1.10:站点公告管理 ==================== */

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
  const count = document.getElementById('noticeCount');
  if (!input || !btn) return;
  if (count) count.textContent = '0 / 100';
  input.addEventListener('input', () => {
    if (count) count.textContent = input.value.length + ' / 100';
  });
  async function send() {
    const body = input.value.trim();
    if (!body) return toast('先写公告内容~');
    btn.disabled = true;
    try {
      await api('POST', '/api/notices/admin', { body });
      input.value = '';
      if (count) count.textContent = '0 / 100';
      toast('公告已发布,前台马上能看到 📢');
      loadNotices();
    } catch (e) { toast('发布失败:' + e.message); }
    finally { btn.disabled = false; }
  }
  btn.addEventListener('click', send);
  // textarea:Enter 换行,Ctrl/⌘+Enter 发布
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); send(); }
  });
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
