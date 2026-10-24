/* ============================================================
   v3.1.0 涂鸦墙:canvas 画板 + 上传 + 展示
   零依赖;只在 contact 页初始化(#doodle 容器存在才干活)
   ============================================================ */
(function () {
  'use strict';

  var canvas = document.getElementById('doodleCanvas');
  var wrap = document.getElementById('doodle');
  if (!canvas || !wrap) return;
  var ctx = canvas.getContext('2d');
  if (!ctx) return;

  // 站点色板(和便签/按钮同一套)
  var COLORS = ['#2d2a32', '#ff6b9d', '#ffd93d', '#2ec4b6', '#9a8bc6', '#6e9fd0', '#e49a62', '#ffffff'];
  var SIZES = [3, 6, 12];
  var color = COLORS[0];
  var size = SIZES[1];
  var drawing = false;
  var undoStack = [];          // dataURL 快照,最多 12 步
  var dirty = false;           // 画过东西才能提交

  var tipEl = document.getElementById('dooTip');
  function tip(msg, warn) {
    if (!tipEl) return;
    tipEl.textContent = msg || '';
    tipEl.classList.toggle('warn', !!warn);
  }

  function paintWhite() {
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }
  function snapshot() {
    try {
      undoStack.push(ctx.getImageData(0, 0, canvas.width, canvas.height));
      if (undoStack.length > 12) undoStack.shift();
    } catch (e) { /* 极端情况忽略 */ }
  }
  paintWhite();

  /* ---- 工具条 ---- */
  var colorsBox = document.getElementById('dooColors');
  var sizesBox = document.getElementById('dooSizes');
  if (colorsBox) {
    colorsBox.innerHTML = COLORS.map(function (c, i) {
      return '<button type="button" class="doo-c' + (i === 0 ? ' active' : '') +
        '" data-c="' + c + '" style="background:' + c + '" aria-label="颜色' + (i + 1) + '"></button>';
    }).join('');
    colorsBox.addEventListener('click', function (e) {
      var b = e.target.closest('.doo-c');
      if (!b) return;
      color = b.getAttribute('data-c');
      colorsBox.querySelectorAll('.doo-c').forEach(function (x) { x.classList.remove('active'); });
      b.classList.add('active');
    });
  }
  if (sizesBox) {
    sizesBox.innerHTML = SIZES.map(function (s, i) {
      return '<button type="button" class="doo-s' + (i === 1 ? ' active' : '') +
        '" data-s="' + s + '" aria-label="笔刷' + (i + 1) + '"><i style="width:' +
        (s + 4) + 'px;height:' + (s + 4) + 'px"></i></button>';
    }).join('');
    sizesBox.addEventListener('click', function (e) {
      var b = e.target.closest('.doo-s');
      if (!b) return;
      size = Number(b.getAttribute('data-s'));
      sizesBox.querySelectorAll('.doo-s').forEach(function (x) { x.classList.remove('active'); });
      b.classList.add('active');
    });
  }

  /* ---- 画笔(pointer 事件同时照顾鼠标和触摸) ---- */
  function pos(ev) {
    var r = canvas.getBoundingClientRect();
    return {
      x: (ev.clientX - r.left) * (canvas.width / r.width),
      y: (ev.clientY - r.top) * (canvas.height / r.height)
    };
  }
  canvas.addEventListener('pointerdown', function (ev) {
    drawing = true;
    dirty = true;
    snapshot();
    canvas.setPointerCapture(ev.pointerId);
    var p = pos(ev);
    ctx.beginPath();
    ctx.moveTo(p.x, p.y);
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    // 单点也画一个点
    ctx.lineTo(p.x + 0.01, p.y + 0.01);
    ctx.strokeStyle = color;
    ctx.lineWidth = size;
    ctx.stroke();
  });
  canvas.addEventListener('pointermove', function (ev) {
    if (!drawing) return;
    var p = pos(ev);
    ctx.lineTo(p.x, p.y);
    ctx.strokeStyle = color;
    ctx.lineWidth = size;
    ctx.stroke();
  });
  ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (n) {
    canvas.addEventListener(n, function () { drawing = false; });
  });
  // 触摸设备上别把画布当滚动垫
  canvas.addEventListener('touchstart', function (e) { e.preventDefault(); }, { passive: false });
  canvas.addEventListener('touchmove', function (e) { e.preventDefault(); }, { passive: false });

  /* ---- 撤销 / 清空 ---- */
  var undoBtn = document.getElementById('dooUndo');
  var clearBtn = document.getElementById('dooClear');
  if (undoBtn) undoBtn.addEventListener('click', function () {
    if (!undoStack.length) { tip('没有可撤销的啦'); return; }
    ctx.putImageData(undoStack.pop(), 0, 0);
  });
  if (clearBtn) clearBtn.addEventListener('click', function () {
    snapshot();
    paintWhite();
    dirty = false;
    tip('');
  });

  /* ---- 提交 ---- */
  var sendBtn = document.getElementById('dooSend');
  if (sendBtn) sendBtn.addEventListener('click', function () {
    if (!dirty) { tip('先画点什么呀~', true); return; }
    sendBtn.disabled = true;
    sendBtn.textContent = '上传中…';
    canvas.toBlob(function (blob) {
      if (!blob) { tip('导出失败,刷新页面再试', true); reset(); return; }
      var fd = new FormData();
      fd.append('file', blob, 'doodle.png');
      fetch('/api/doodles', { method: 'POST', body: fd })
        .then(function (r) { return r.json().then(function (d) { return { s: r.status, d: d }; }); })
        .then(function (r) {
          if (r.s === 200 && r.d.ok) {
            tip('画好啦!审核通过就会贴上墙 ~');
            undoStack = [];
            paintWhite();
            dirty = false;
          } else {
            tip(r.d.error || '上传失败,待会儿再试试', true);
          }
        })
        .catch(function () { tip('网络开小差了,再试一次?', true); })
        .then(reset);
    }, 'image/png');
    function reset() {
      sendBtn.disabled = false;
      sendBtn.textContent = '📮 交涂鸦';
    }
  });

  /* ---- 涂鸦墙展示 + 点击放大 ---- */
  var grid = document.getElementById('doodleGrid');
  function loadWall() {
    if (!grid) return;
    fetch('/api/doodles').then(function (r) { return r.json(); })
      .then(function (d) {
        var list = d.doodles || [];
        if (!list.length) {
          grid.innerHTML = '<p class="hint" style="text-align:center">墙上还空着,第一张就是你的~</p>';
          return;
        }
        grid.innerHTML = list.map(function (x) {
          return '<button type="button" class="doodle-cell" data-url="' + escAttr(x.url) + '"' +
            ' aria-label="看大图"><img src="' + escAttr(x.url) + '" loading="lazy" alt="访客涂鸦" /></button>';
        }).join('');
      })
      .catch(function () { });
  }
  if (grid) grid.addEventListener('click', function (e) {
    var cell = e.target.closest('.doodle-cell');
    if (!cell) return;
    var ov = document.createElement('div');
    ov.className = 'qr-overlay';
    ov.innerHTML = '<div class="card qr-box"><button class="qr-close" aria-label="关闭">✕</button>' +
      '<img class="egg-art" src="' + cell.getAttribute('data-url') + '" alt="涂鸦大图" /></div>';
    document.body.appendChild(ov);
    requestAnimationFrame(function () { ov.classList.add('open'); });
    function close() { ov.classList.remove('open'); setTimeout(function () { ov.remove(); }, 250); }
    ov.addEventListener('click', function (ev) { if (ev.target === ov) close(); });
    ov.querySelector('.qr-close').addEventListener('click', close);
    document.addEventListener('keydown', function esc(ev) {
      if (ev.key === 'Escape') { close(); document.removeEventListener('keydown', esc); }
    });
  });
  loadWall();
})();
