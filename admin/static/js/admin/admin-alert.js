/* ============================================================
   后台 · admin-alert:新留言/新追问 实时提醒(v2.7.1)
   - 轮询 /api/admin/alerts(轻量,只返计数+摘要)
   - 只在「待审数量变多」时弹窗,首次加载只建基线不打扰
   - 页面隐藏时暂停轮询,回到前台立刻补一次
   ============================================================ */
'use strict';

const ALERT_POLL_MS = 20000;     // 轮询间隔
const ALERT_AUTO_HIDE = 9000;    // 弹窗自动消失

let _alertBase = null;           // {pm, pt} 上次已知的待审数
let _alertTimer = null;
let _alertHideTimer = null;

/* ---------- 弹窗 DOM(懒创建,避免改动 admin.html 结构) ---------- */
function _alertEl() {
  let box = document.getElementById('adminAlert');
  if (box) return box;
  box = document.createElement('div');
  box.id = 'adminAlert';
  box.className = 'admin-alert';
  box.innerHTML =
    '<div class="aa-head"><b class="aa-title">🔔 新消息</b>' +
    '<button class="aa-close" type="button" aria-label="关闭">✕</button></div>' +
    '<div class="aa-body"></div>' +
    '<div class="aa-foot"><button class="aa-go" type="button">去看看</button></div>';
  document.body.appendChild(box);
  box.querySelector('.aa-close').addEventListener('click', hideAdminAlert);
  box.querySelector('.aa-go').addEventListener('click', () => {
    hideAdminAlert();
    if (typeof showPanel === 'function') showPanel('messages');
  });
  return box;
}

function hideAdminAlert() {
  const box = document.getElementById('adminAlert');
  if (box) box.classList.remove('show');
  clearTimeout(_alertHideTimer);
}

function showAdminAlert(title, lines) {
  const box = _alertEl();
  box.querySelector('.aa-title').textContent = title;
  box.querySelector('.aa-body').innerHTML = lines
    .map(l => '<p class="aa-line">' + l + '</p>').join('');
  box.classList.add('show');
  clearTimeout(_alertHideTimer);
  _alertHideTimer = setTimeout(hideAdminAlert, ALERT_AUTO_HIDE);
}

/* ---------- 轮询 ---------- */
async function pollAlerts() {
  let d;
  try {
    d = await api('GET', '/api/admin/alerts');
  } catch (e) {
    return;                       // 401 由 api() 处理跳登录;网络抖动静默
  }
  const pm = d.pending_messages || 0;
  const pt = d.pending_threads || 0;

  // 首次:只记基线,不弹
  if (_alertBase === null) {
    _alertBase = { pm, pt };
    syncMsgBadge(pm + pt);
    return;
  }

  const newMsg = pm > _alertBase.pm;
  const newThr = pt > _alertBase.pt;
  _alertBase = { pm, pt };
  syncMsgBadge(pm + pt);

  if (!newMsg && !newThr) return;

  const lines = [];
  let title = '🔔 新消息';
  if (newMsg) {
    const m = d.latest_message;
    title = '💌 收到新留言';
    lines.push('来自 <b>' + esc(m && m.name || '匿名') + '</b>');
    if (m && m.body) lines.push('「' + esc(m.body.slice(0, 60)) +
      (m.body.length > 60 ? '…' : '') + '」');
    if (pm > 1) lines.push('还有 ' + (pm - 1) + ' 条待审留言');
  }
  if (newThr) {
    const t = d.latest_thread;
    if (!newMsg) title = '💬 收到新追问';
    lines.push('留言人追问:' + (t && t.body ? '「' + esc(t.body.slice(0, 60)) +
      (t.body.length > 60 ? '…' : '') + '」' : ''));
    if (pt > 1) lines.push('还有 ' + (pt - 1) + ' 条待审追问');
  }
  showAdminAlert(title, lines);

  // 顺手刷新留言面板(如果正开着)
  const panel = document.getElementById('panel-messages');
  if (panel && panel.classList.contains('active') && typeof loadMessages === 'function') {
    loadMessages();
  }
}

/* 侧边栏角标:待审总数 */
function syncMsgBadge(n) {
  const cnt = document.getElementById('cnt-messages');
  if (cnt) cnt.textContent = n || '0';
  cnt && cnt.classList.toggle('has-new', n > 0);
}

function startAlertPolling() {
  if (_alertTimer) return;
  pollAlerts();
  _alertTimer = setInterval(pollAlerts, ALERT_POLL_MS);
  document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
      clearInterval(_alertTimer); _alertTimer = null;
    } else if (!_alertTimer) {
      pollAlerts();
      _alertTimer = setInterval(pollAlerts, ALERT_POLL_MS);
    }
  });
}

startAlertPolling();
