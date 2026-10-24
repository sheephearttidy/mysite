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

  if (new1 !== new2) { showPerr('两次入入的新密码不一样'); return; }
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
    const tpEl = document.getElementById('msgThreadPending');
    if (tpEl) tpEl.textContent = c.thread_pending ?? 0;
    const cnt = document.getElementById('cnt-messages');
    if (cnt) {
      const n = (c.pending || 0) + (c.thread_pending || 0);
      cnt.textContent = n ? `待审${n}` : c.total;
    }

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
        ${(m.threads && m.threads.length) ? `<div class="mai-thread">${m.threads.map(t => `
          <div class="mai-turn ${t.role}">
            <span class="mai-who">${t.role === 'owner' ? '🧑‍💻 站主' : '💬 留言人'}</span>
            <span class="mai-turntext">${esc(t.body)}</span>
            ${t.role === 'guest' ? `
              <span class="badge ${MSG_STATE_CLS[t.shown]}">${MSG_STATE[t.shown]}</span>
              ${t.shown !== 1 ? `<button class="op save" onclick="msgThreadMod(${m.id},${t.id},'show')">公开</button>` : ''}
              ${t.shown === 1 ? `<button class="op" onclick="msgThreadMod(${m.id},${t.id},'hide')">隐藏</button>` : ''}
              <button class="op del" onclick="msgThreadDel(${m.id},${t.id})">删</button>` : ''}
          </div>`).join('')}</div>` : ''}
        <div class="mai-reply-box">
          <textarea class="sf-input mai-reply-input" rows="2" maxlength="140"
            placeholder="站主回复(140 字内,回车发送,Shift+回车换行)"></textarea>
          <button class="op save" onclick="msgReplyInline(${m.id}, this)">💬 发送回复</button>
        </div>
        <div class="ops" style="margin-top:8px">
          ${m.shown !== 1 ? `<button class="op save" onclick="msgMod(${m.id},'show')">✅ 展示</button>` : ''}
          ${m.shown === 1 ? `<button class="op" onclick="msgMod(${m.id},'hide')">🙈 隐藏</button>` : ''}
          ${m.shown === 2 ? `<button class="op" onclick="msgMod(${m.id},'pending')">↩️ 转待审</button>` : ''}
          <button class="op del" onclick="msgDel(${m.id})">🗑️ 删除留言</button>
        </div>
      </div>`).join('');

    // 回车发送(Shift+回车换行)
    list.querySelectorAll('.mai-reply-input').forEach(ta => {
      ta.addEventListener('keydown', ev => {
        if (ev.key === 'Enter' && !ev.shiftKey) {
          ev.preventDefault();
          msgReplyInline(Number(ta.closest('.msg-admin-item').dataset.id), ta);
        }
      });
    });
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

/* v2.7.0:内联回复框(替代 prompt 弹窗) */
async function msgReplyInline(id, btn) {
  const box = btn.closest('.mai-reply-box');
  const ta = box.querySelector('.mai-reply-input');
  const text = (ta.value || '').trim();
  if (!text) { ta.focus(); return; }
  btn.disabled = true;
  try {
    const r = await fetch(`/api/messages/${id}/mod`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ action: 'reply', reply: text })
    });
    const d = await r.json();
    if (!d.ok) return alert(d.error || '回复失败');
    loadMessages();
  } finally {
    btn.disabled = false;
  }
}

/* v2.7.0:审核访客追问 */
async function msgThreadMod(mid, tid, action) {
  const r = await fetch(`/api/messages/${mid}/mod`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'thread_' + action, tid })
  });
  const d = await r.json();
  if (!d.ok) return alert(d.error || '操作失败');
  loadMessages();
}

async function msgThreadDel(mid, tid) {
  if (!confirm('删除这条追问?')) return;
  const r = await fetch(`/api/messages/${mid}/mod`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action: 'thread_delete', tid })
  });
  const d = await r.json();
  if (!d.ok) return alert(d.error || '删除失败');
  loadMessages();
}

function msgReply(id, current) {
  const reply = prompt('入入站主回复(留空清除回复,最多 140 字):', current || '');
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

/* ==================== v3.1.0:提问箱管理 ==================== */

const Q_STATE = { 0: '待回答', 1: '已公开', 2: '已隐藏' };

async function loadQuestions() {
  try {
    const d = await api('GET', '/api/questions/admin');
    const c = d.counts || {};
    document.getElementById('qPending').textContent = c.pending ?? 0;
    document.getElementById('qShownN').textContent = c.shown ?? 0;
    document.getElementById('qTotalN').textContent = c.total ?? 0;
    const cnt = document.getElementById('cnt-questions');
    if (cnt) cnt.textContent = c.pending ? `待答${c.pending}` : c.total;

    const list = document.getElementById('qAdminList');
    if (!d.questions.length) {
      list.innerHTML = '<p class="hint">还没人提问,去前台「来找我玩」页问问看~</p>';
      return;
    }
    list.innerHTML = d.questions.map(q => `
      <div class="msg-admin-item" data-id="${q.id}">
        <div class="mai-head">
          <b>🫥 匿名</b>
          <span class="badge ${MSG_STATE_CLS[q.shown]}">${Q_STATE[q.shown]}</span>
          <span class="hint">${fmtMsgTime(q.ts)} · ${esc(q.ip || '未知IP')}</span>
        </div>
        <div class="mai-body">${esc(q.body)}</div>
        ${q.answer ? `<div class="mai-thread">
          <div class="mai-turn owner">
            <span class="mai-who">🧑‍💻 我的回答</span>
            <span class="mai-turntext">${esc(q.answer)}</span>
          </div></div>` : ''}
        <div class="mai-reply-box">
          <textarea class="sf-input mai-reply-input" rows="2" maxlength="500"
            placeholder="${q.answer ? '改写回答(回车提交,Shift+回车换行)' : '写下回答(500 字内,回车提交,回答即公开)'}">${q.answer ? esc(q.answer) : ''}</textarea>
          <button class="op save" onclick="qAnswerInline(${q.id}, this)">💬 提交回答</button>
        </div>
        <div class="ops" style="margin-top:8px">
          ${q.shown !== 1 ? `<button class="op save" onclick="qMod(${q.id},'show')">✅ 公开</button>` : ''}
          ${q.shown === 1 ? `<button class="op" onclick="qMod(${q.id},'hide')">🙈 隐藏</button>` : ''}
          ${q.shown === 2 ? `<button class="op" onclick="qMod(${q.id},'pending')">↩️ 移回待答</button>` : ''}
          <button class="op del" onclick="qDel(${q.id})">🗑️ 删除</button>
        </div>
      </div>`).join('');

    // 回车提交(Shift+回车换行)
    list.querySelectorAll('.mai-reply-input').forEach(ta => {
      ta.addEventListener('keydown', ev => {
        if (ev.key === 'Enter' && !ev.shiftKey) {
          ev.preventDefault();
          qAnswerInline(Number(ta.closest('.msg-admin-item').dataset.id), ta);
        }
      });
    });
  } catch (e) {
    console.error('loadQuestions', e);
  }
}

async function qAnswerInline(id, btn) {
  const box = btn.closest('.mai-reply-box');
  const ta = box.querySelector('.mai-reply-input');
  const txt = (ta.value || '').trim();
  if (!txt) { ta.focus(); return; }
  btn.disabled = true;
  try {
    const d = await api('POST', `/api/questions/${id}/mod`,
      { action: 'answer', answer: txt });
    toast('已回答并公开 ✅ 前台刷新可见');
    loadQuestions();
  } catch (e) {
    toast('提交失败:' + e.message);
  } finally {
    btn.disabled = false;
  }
}

async function qMod(id, action) {
  try {
    await api('POST', `/api/questions/${id}/mod`, { action });
    loadQuestions();
  } catch (e) { toast('操作失败:' + e.message); }
}

async function qDel(id) {
  if (!confirm('删掉这条提问?(连同回答一起删)')) return;
  qMod(id, 'delete');
}

/* ==================== v3.1.0:涂鸦墙管理 ==================== */

async function loadDoodles() {
  try {
    const d = await api('GET', '/api/doodles/admin');
    const c = d.counts || {};
    document.getElementById('dooPending').textContent = c.pending ?? 0;
    document.getElementById('dooShownN').textContent = c.shown ?? 0;
    document.getElementById('dooTotalN').textContent = c.total ?? 0;
    const cnt = document.getElementById('cnt-doodles');
    if (cnt) cnt.textContent = c.pending ? `待审${c.pending}` : c.total;

    const list = document.getElementById('dooAdminList');
    if (!d.doodles.length) {
      list.innerHTML = '<p class="hint">还没收到涂鸦,去前台画板画一张试试~</p>';
      return;
    }
    list.innerHTML = d.doodles.map(x => `
      <div class="doo-admin-item" data-id="${x.id}">
        <a href="${x.url}" target="_blank" rel="noopener" class="doo-thumb">
          <img src="${x.url}" loading="lazy" alt="涂鸦 ${x.id}" /></a>
        <div class="doo-meta">
          <span class="badge ${MSG_STATE_CLS[x.shown]}">${MSG_STATE[x.shown]}</span>
          <span class="hint">${fmtMsgTime(x.ts)} · ${esc(x.ip || '未知IP')} · ${x.width}×${x.height}</span>
          <div class="ops" style="margin-top:8px">
            ${x.shown !== 1 ? `<button class="op save" onclick="dooMod(${x.id},'show')">✅ 展示</button>` : ''}
            ${x.shown === 1 ? `<button class="op" onclick="dooMod(${x.id},'hide')">🙈 隐藏</button>` : ''}
            <button class="op del" onclick="dooMod(${x.id},'delete')">🗑️ 删除(连文件)</button>
          </div>
        </div>
      </div>`).join('');
  } catch (e) {
    console.error('loadDoodles', e);
  }
}

async function dooMod(id, action) {
  if (action === 'delete' && !confirm('删掉这张涂鸦?图片文件会一起删除')) return;
  try {
    await api('POST', `/api/doodles/${id}/mod`, { action });
    loadDoodles();
  } catch (e) { toast('操作失败:' + e.message); }
}
