/* ============================================================
   后台 · admin-app:收尾初始化 + 两步验证 2FA(v2.1 拆分)
   ============================================================ *//* ==================== v2.0:两步验证(2FA) ==================== */

async function twofaRefresh() {
  try {
    const s = await api('GET', '/api/security/2fa/status');
    const card = document.getElementById('secCard2fa');
    const val = document.getElementById('sc2faVal');
    if (val) val.textContent = s.enabled ? '已启用 ✅' : '未启用';
    if (card) card.classList.toggle('ok', !!s.enabled);
  } catch (e) { /* 面板未打开时静默 */ }
}

async function twofaStart() {
  try {
    const d = await api('GET', '/api/security/2fa/setup');
    const box = document.getElementById('twofaBox');
    box.style.display = 'block';
    // v2.0.1 修复:qrcode.min.js 需要容器 div(往里塞 canvas),
    // 此前误传 <img> 导致二维码画不出来
    const holder = document.getElementById('qrBox');
    if (typeof QRCode === 'undefined') {
      holder.innerHTML = '<p class="hint" style="padding:10px">二维码组件没加载出来,刷新页面再试</p>';
      return;
    }
    holder.innerHTML = '';
    new QRCode(holder, { text: d.uri, width: 172, height: 172,
                         correctLevel: QRCode.CorrectLevel.M });
  } catch (e) { toast('生成失败:' + e.message); }
}

async function twofaConfirm() {
  const code = document.getElementById('twofaCode').value.trim();
  if (!/^\d{6}$/.test(code)) return toast('请输入 6 位数字动态码');
  try {
    await api('POST', '/api/security/2fa/enable', { code });
    document.getElementById('twofaBox').style.display = 'none';
    document.getElementById('twofaCode').value = '';
    toast('两步验证已启用!下次登录要用上它啦 🔐');
    twofaRefresh();
  } catch (e) { toast('启用失败:' + e.message); }
}

async function twofaOff() {
  const code = prompt('输入当前 6 位动态码以确认关闭两步验证:');
  if (code === null) return;
  try {
    await api('POST', '/api/security/2fa/disable', { code: code.trim() });
    toast('两步验证已关闭');
    twofaRefresh();
  } catch (e) { toast('关闭失败:' + e.message); }
}

// sec-pass 面板打开时刷新 2FA 状态
const _origShowPanel = showPanel;
showPanel = function (name) {
  _origShowPanel(name);
  if (name === 'sec-pass') twofaRefresh();
};

// 分组折叠状态恢复(原 961 行的重复 renderAll() 已删,幂等无意义)
restoreGroups();
