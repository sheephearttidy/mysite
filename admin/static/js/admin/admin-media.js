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

/* ============================================================
   相册管理(v3.0.0)
   ============================================================ */
let _photoCache = [];

async function loadGallery() {
  const box = document.getElementById('galleryList');
  const stat = document.getElementById('galleryStat');
  if (!box) return;
  try {
    const r = await api('GET', '/api/photos/admin');
    _photoCache = r.photos || [];
    const shownN = _photoCache.filter(p => p.shown).length;
    if (stat) stat.textContent = `共 ${_photoCache.length} 张,公开 ${shownN} 张`;
    const cnt = document.getElementById('cnt-gallery');
    if (cnt) cnt.textContent = _photoCache.length;

    if (!_photoCache.length) {
      box.innerHTML = '<p class="hint">相册还是空的,点上面「从图片库添加」挑几张吧~</p>';
      return;
    }
    box.innerHTML = _photoCache.map(p => `
      <div class="ph-admin-item" data-id="${p.id}">
        <img class="ph-thumb" src="${escAttr(p.url)}" alt="" loading="lazy" />
        <div class="ph-fields">
          <input class="sf-input ph-t" maxlength="80" placeholder="标题(可留空)"
                 value="${escAttr(p.title || '')}" />
          <input class="sf-input ph-c" maxlength="20" placeholder="分类,如 校园/旅行/日常"
                 value="${escAttr(p.category || '')}" />
          <input class="sf-input ph-d" maxlength="500" placeholder="描述(可留空)"
                 value="${escAttr(p.desc || '')}" />
          <div class="ph-row">
            <input class="sf-input ph-s" type="date" value="${escAttr(p.shot_at || '')}" />
            <input class="sf-input ph-o" type="number" placeholder="排序" style="max-width:90px"
                   value="${p.sort || 0}" />
            <label class="ph-sw">
              <input type="checkbox" ${p.shown ? 'checked' : ''} onchange="togglePhoto(${p.id}, this.checked)" />
              前台可见
            </label>
          </div>
        </div>
        <div class="ph-ops">
          <button class="op save" onclick="savePhoto(${p.id}, this)">💾 保存</button>
          <button class="op del" onclick="removePhoto(${p.id})">🗑️ 移出相册</button>
        </div>
      </div>`).join('');
  } catch (e) {
    box.innerHTML = '<p class="hint">加载失败:' + esc(e.message) + '</p>';
  }
}

async function savePhoto(id, btn) {
  const item = btn.closest('.ph-admin-item');
  const body = {
    title: item.querySelector('.ph-t').value,
    category: item.querySelector('.ph-c').value,
    desc: item.querySelector('.ph-d').value,
    shot_at: item.querySelector('.ph-s').value,
    sort: Number(item.querySelector('.ph-o').value || 0)
  };
  btn.disabled = true;
  try {
    await api('PUT', '/api/photos/' + id, body);
    toast('已保存 ✅');
    loadGallery();
  } catch (e) { toast('保存失败:' + e.message); }
  finally { btn.disabled = false; }
}

async function togglePhoto(id, on) {
  try {
    await api('PUT', '/api/photos/' + id, { shown: on });
    toast(on ? '前台可见' : '已隐藏');
  } catch (e) { toast('操作失败:' + e.message); loadGallery(); }
}

async function removePhoto(id) {
  if (!confirm('从相册移除这张?(图片文件会留在图片库里)')) return;
  try {
    await api('DELETE', '/api/photos/' + id);
    toast('已移出相册');
    loadGallery();
  } catch (e) { toast('操作失败:' + e.message); }
}

/* 从图片库挑图加入相册 */
async function openPhotoPick() {
  let items = [];
  try {
    const r = await api('GET', '/api/uploads');
    items = r.items || [];
  } catch (e) { return toast('读取图片库失败:' + e.message); }
  if (!items.length) return toast('图片库还是空的,先去「图片库」传几张');

  const inAlbum = new Set(_photoCache.map(p => p.file));
  const html = items.map(it => `
    <label class="ph-pick-item ${inAlbum.has(it.name) ? 'used' : ''}">
      <input type="checkbox" value="${escAttr(it.name)}"
             ${inAlbum.has(it.name) ? 'disabled' : ''} />
      <img src="${escAttr(it.url)}" alt="" loading="lazy" />
      <span class="ph-pick-meta">${inAlbum.has(it.name) ? '已在相册' : (it.size / 1024).toFixed(0) + ' KB'}</span>
    </label>`).join('');

  const box = document.getElementById('photoPickBox');
  box.querySelector('.ph-pick-grid').innerHTML = html;
  box.classList.add('show');
}

async function confirmPhotoPick() {
  const box = document.getElementById('photoPickBox');
  const names = [...box.querySelectorAll('input[type=checkbox]:checked')].map(i => i.value);
  if (!names.length) return toast('还没选图片');
  let ok = 0;
  for (const name of names) {
    try {
      await api('POST', '/api/photos', { file: name });
      ok++;
    } catch (e) { /* 单张失败继续 */ }
  }
  box.classList.remove('show');
  toast(`已加入相册 ${ok} 张`);
  loadGallery();
}

function closePhotoPick() {
  document.getElementById('photoPickBox').classList.remove('show');
}
