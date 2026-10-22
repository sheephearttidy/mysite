/* ============================================================
   后台 · admin-content:内容管理(技能树/时间线/统计/项目墙/
   个人信息)的列表渲染 + 编辑/删除表单(v2.1 拆分)
   ============================================================ */function renderSkills() {
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

/* ---------- v2.2 三个新内容类型的渲染 ---------- */
const HONOR_LEVEL = { national:'国家级', provincial:'省级', school:'校级', other:'其他' };
const NOTE_MOOD_TXT = { teal:'薄荷绿', pink:'粉', yellow:'黄', purple:'紫', blue:'蓝', orange:'橙' };

function renderHonors() {
  const box = document.getElementById('list-honors');
  if (!box) return;
  box.innerHTML = DATA.honors.map(h => `
    <div class="item">
      <div class="item-top">
        <span class="badge serious">${esc(h.emoji)} ${HONOR_LEVEL[h.level] || h.level}</span>
        <span class="meta">#${h.sort}</span>
      </div>
      <h3>${esc(h.title)}</h3>
      <div class="meta">${esc(h.year)}</div>
      ${h.desc ? `<div class="note">${esc(h.desc)}</div>` : ''}
      <div class="ops">
        <button class="op edit" onclick="editItem('honors', ${h.id})">✏️ 编辑</button>
        <button class="op del" onclick="delItem('honors', ${h.id})">🗑️ 删除</button>
      </div>
    </div>`).join('') || '<p class="hint">荣誉墙还是空的,拿奖了记得来晒晒~</p>';
}

function renderNotes() {
  const box = document.getElementById('list-notes');
  if (!box) return;
  box.innerHTML = DATA.notes.map(n => `
    <div class="item">
      <div class="item-top">
        <span class="badge passive">${esc(n.emoji)} ${NOTE_MOOD_TXT[n.mood] || n.mood}</span>
        <span class="meta">${new Date(n.ts * 1000).toLocaleDateString('zh-CN')}</span>
      </div>
      <h3 style="font-size:15px">${esc(n.text)}</h3>
      <div class="ops">
        <button class="op edit" onclick="editItem('notes', ${n.id})">✏️ 编辑</button>
        <button class="op del" onclick="delItem('notes', ${n.id})">🗑️ 删除</button>
      </div>
    </div>`).join('') || '<p class="hint">还没记过随手记,记一笔吧~</p>';
}

function renderFriendlinks() {
  const box = document.getElementById('list-friendlinks');
  if (!box) return;
  box.innerHTML = DATA.friendlinks.map(f => `
    <div class="item">
      <div class="item-top">
        <span class="badge serious">${esc(f.emoji)} ${esc(f.name)}</span>
        <span class="meta">#${f.sort}</span>
      </div>
      <div class="note">🔗 ${esc(f.url)}</div>
      ${f.desc ? `<div class="note">${esc(f.desc)}</div>` : ''}
      <div class="ops">
        <button class="op edit" onclick="editItem('friendlinks', ${f.id})">✏️ 编辑</button>
        <button class="op del" onclick="delItem('friendlinks', ${f.id})">🗑️ 删除</button>
      </div>
    </div>`).join('') || '<p class="hint">还没有友链,加一个吧~</p>';
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
  // v2.2 荣誉墙
  honors: [
    { k:'emoji',  label:'图标 emoji',        type:'text' },
    { k:'year',   label:'年份(如 2025 / 2024.11)', type:'text' },
    { k:'title',  label:'奖项名称',           type:'text' },
    { k:'desc',   label:'一句话说明(可空)',  type:'text' },
    { k:'level',  label:'级别',              type:'select',
      opts:{national:'国家级', provincial:'省级', school:'校级', other:'其他'} },
    { k:'sort',   label:'排序(小的在前)',    type:'number' },
  ],
  // v2.2 随手记
  notes: [
    { k:'emoji', label:'图标 emoji',         type:'text' },
    { k:'text',  label:'想说什么',           type:'textarea' },
    { k:'mood',  label:'便签颜色',           type:'select',
      opts:{teal:'薄荷绿', pink:'粉', yellow:'黄', purple:'紫', blue:'蓝', orange:'橙'} },
  ],
  // v2.2 友情链接
  friendlinks: [
    { k:'name', label:'站名',               type:'text' },
    { k:'url',  label:'网址(https://…)',    type:'text' },
    { k:'emoji',label:'图标 emoji',         type:'text' },
    { k:'desc', label:'一句话介绍(可空)',  type:'text' },
    { k:'sort', label:'排序(小的在前)',     type:'number' },
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
