/* ============================================================
   前台 · gallery:相册页(v3.0.0)
   - 瀑布流(多列布局,每张按自己比例撑高)
   - 分类筛选
   - 灯箱:点开看大图,支持左右切换、键盘 Esc/←/→、点背景关闭
   ============================================================ */
(function () {
  'use strict';

  var grid = document.getElementById('galGrid');
  if (!grid) return;

  var filterBox = document.getElementById('galFilter');
  var emptyEl = document.getElementById('galEmpty');
  var loadingEl = document.getElementById('galLoading');
  var lb = document.getElementById('galLightbox');
  var lbImg = document.getElementById('galLbImg');
  var lbTitle = document.getElementById('galLbTitle');
  var lbDesc = document.getElementById('galLbDesc');
  var lbMeta = document.getElementById('galLbMeta');

  var photos = [];
  var shown = [];          // 当前筛选后的列表(灯箱切换用)
  var cur = -1;            // 灯箱当前索引
  var activeCat = '';      // 当前分类

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  }

  function fmtDate(s) {
    if (!s) return '';
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s);
    if (!m) return s;
    return m[1] + '年' + Number(m[2]) + '月' + Number(m[3]) + '日';
  }

  /* ---------- 渲染照片墙 ---------- */
  function render() {
    shown = activeCat ? photos.filter(function (p) { return p.category === activeCat; })
                      : photos;
    grid.innerHTML = '';
    emptyEl.hidden = shown.length > 0 || photos.length === 0;
    if (!shown.length) {
      emptyEl.hidden = photos.length > 0;   // 有图但该分类没图时提示
      if (photos.length > 0 && activeCat) {
        emptyEl.hidden = false;
        emptyEl.textContent = '「' + activeCat + '」里还没有照片';
      }
      return;
    }
    emptyEl.hidden = true;

    shown.forEach(function (p, i) {
      var fig = document.createElement('figure');
      fig.className = 'gal-item';
      fig.setAttribute('data-idx', i);
      fig.setAttribute('role', 'button');
      fig.setAttribute('tabindex', '0');
      // 有宽高就按比例预留,避免加载时跳动
      var ratio = (p.width && p.height) ? (p.width / p.height) : 0;
      var pad = ratio ? (100 / ratio) : 66.7;
      var title = p.title ? '<figcaption class="gal-cap">' + esc(p.title) + '</figcaption>' : '';
      fig.innerHTML =
        '<div class="gal-imgwrap" style="padding-top:' + pad.toFixed(3) + '%">' +
        '<img src="' + esc(p.url) + '" alt="' + esc(p.title || '照片') + '" loading="lazy" />' +
        '</div>' + title;
      grid.appendChild(fig);
    });

    // 进场动画(逐个淡入)
    var io = 'IntersectionObserver' in window
      ? new IntersectionObserver(function (es) {
          es.forEach(function (e) {
            if (e.isIntersecting) {
              e.target.classList.add('in');
              io.unobserve(e.target);
            }
          });
        }, { threshold: 0.08 })
      : null;
    [].forEach.call(grid.querySelectorAll('.gal-item'), function (el, i) {
      if (io) io.observe(el);
      else el.classList.add('in');
    });
  }

  /* ---------- 分类筛选 ---------- */
  function renderFilter(cats) {
    if (!cats || !cats.length) { filterBox.hidden = true; return; }
    filterBox.hidden = false;
    var html = '<button class="gal-chip on" data-cat="">全部 <i>' + photos.length + '</i></button>';
    cats.forEach(function (c) {
      html += '<button class="gal-chip" data-cat="' + esc(c.name) + '">' +
              esc(c.name) + ' <i>' + c.count + '</i></button>';
    });
    filterBox.innerHTML = html;
    [].forEach.call(filterBox.querySelectorAll('.gal-chip'), function (btn) {
      btn.addEventListener('click', function () {
        activeCat = btn.getAttribute('data-cat') || '';
        [].forEach.call(filterBox.querySelectorAll('.gal-chip'), function (b) {
          b.classList.toggle('on', b === btn);
        });
        render();
      });
    });
  }

  /* ---------- 灯箱 ---------- */
  function openLb(idx) {
    if (idx < 0 || idx >= shown.length) return;
    cur = idx;
    var p = shown[idx];
    lbImg.src = p.url;
    lbImg.alt = p.title || '照片';
    lbTitle.textContent = p.title || '';
    lbDesc.textContent = p.desc || '';
    var bits = [];
    if (p.shot_at) bits.push('📅 ' + fmtDate(p.shot_at));
    if (p.category) bits.push('🏷️ ' + p.category);
    lbMeta.textContent = bits.join('  ');
    // v3.0.1:改用 class 控制显隐(不再碰 hidden 属性,
    // 避免 display:flex 覆盖 [hidden] 导致灯箱常驻)
    lb.classList.add('show');
    document.body.classList.add('lb-open');
    // 只有一张时不显示左右
    var multi = shown.length > 1;
    document.getElementById('galLbPrev').hidden = !multi;
    document.getElementById('galLbNext').hidden = !multi;
  }

  function closeLb() {
    lb.classList.remove('show');
    document.body.classList.remove('lb-open');
    lbImg.src = '';
    cur = -1;
  }

  function stepLb(d) {
    if (cur < 0) return;
    var n = shown.length;
    openLb((cur + d + n) % n);
  }

  grid.addEventListener('click', function (e) {
    var fig = e.target.closest('.gal-item');
    if (fig) openLb(Number(fig.getAttribute('data-idx')));
  });
  grid.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var fig = e.target.closest('.gal-item');
    if (fig) { e.preventDefault(); openLb(Number(fig.getAttribute('data-idx'))); }
  });

  document.getElementById('galLbClose').addEventListener('click', closeLb);
  document.getElementById('galLbPrev').addEventListener('click', function (e) { e.stopPropagation(); stepLb(-1); });
  document.getElementById('galLbNext').addEventListener('click', function (e) { e.stopPropagation(); stepLb(1); });
  lb.addEventListener('click', function (e) {
    if (e.target === lb) closeLb();     // 点背景关闭
  });
  document.addEventListener('keydown', function (e) {
    if (!lb.classList.contains('show')) return;
    if (e.key === 'Escape') closeLb();
    else if (e.key === 'ArrowLeft') stepLb(-1);
    else if (e.key === 'ArrowRight') stepLb(1);
  });

  /* ---------- 加载数据 ---------- */
  function load() {
    fetch('/api/gallery').then(function (r) { return r.json(); })
      .then(function (d) {
        photos = d.photos || [];
        loadingEl.hidden = true;
        if (!photos.length) {
          emptyEl.hidden = false;
          emptyEl.textContent = '相册还空着,等拍了好看的照片再放上来 🌱';
          return;
        }
        renderFilter(d.categories || []);
        render();
      })
      .catch(function () {
        loadingEl.textContent = '照片加载失败,刷新试试~';
      });
  }

  load();
})();
