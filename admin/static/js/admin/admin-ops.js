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

/* ==================== v1.9.0:留言板管理 ==================== *//* ==================== v1.9.0:留言板管理 ==================== */

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
