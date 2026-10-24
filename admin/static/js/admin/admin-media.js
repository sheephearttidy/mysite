/* ============================================================
   后台 · admin-media:图片上传/图片库/数据导入(v2.1 拆分)
   ============================================================ *//* ---------- 图片上传 ---------- */
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
  if (!confirm(replace ? '⚠️ 确定清空并恢复?' : '确定用这个件件恢复内容吗?')) return;
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
    toast('件件读取失败,确认是导出的 JSON 吗? 😵');
  }
}
