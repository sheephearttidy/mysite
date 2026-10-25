/* ============================================================
   v1.9.1 氛围包:主题色换肤 + 时间问候
   与 theme.js 的暗色系统独立共存(换品牌色,不动明暗)
   ============================================================ */

(function () {
  'use strict';

  /* ===================== 主题色换肤 ===================== */
  /* 六套预设品牌色。v3.2.1 修 bug:以前 applyAccent 直接内联改写
     --pink/--pink-bg 本体,内联优先级高于 dark.css 的 [data-theme] 覆盖,
     暗色下一切色整站粉色系被打回亮色值(亮粉压暗底,刺眼)。
     现在改写间接变量 --accent-pink/--accent-pink-bg(--pink 桥接它们),
     且每套主题带暗色版色值,按当前明暗应用;监听明暗切换时重写。 */
  var THEMES = [
    { key: 'candy',  name: '🍬 奶糖粉',
      pink: '#ff6b9d', bg: '#ffe4ef', shadow: '#c94f76', hl: 'rgba(255, 217, 61, 0.95)',
      darkPink: '#d488a6', darkBg: '#4a2f3d' },
    { key: 'mint',   name: '🌿 薄荷绿',
      pink: '#2fa886', bg: '#e0f4ee', shadow: '#1f7d64', hl: 'rgba(120, 220, 190, 0.5)',
      darkPink: '#6fb5ab', darkBg: '#25403c' },
    { key: 'sky',    name: '☁️ 天空蓝',
      pink: '#4a90d9', bg: '#e2edf9', shadow: '#2f6dad', hl: 'rgba(140, 195, 250, 0.5)',
      darkPink: '#7ba3c4', darkBg: '#26333f' },
    { key: 'grape',  name: '🍇 葡萄紫',
      pink: '#8b6bd9', bg: '#ebe5f9', shadow: '#6a4cb5', hl: 'rgba(190, 170, 245, 0.5)',
      darkPink: '#9d8fc4', darkBg: '#352d47' },
    { key: 'honey',  name: '🍯 蜂蜜橙',
      pink: '#e88a3a', bg: '#fdeede', shadow: '#b56722', hl: 'rgba(250, 205, 140, 0.55)',
      darkPink: '#d19a70', darkBg: '#453222' },
    { key: 'sakura', name: '🌸 樱花木',
      pink: '#c96b85', bg: '#f9e4ea', shadow: '#a34a66', hl: 'rgba(240, 180, 200, 0.55)',
      darkPink: '#c48a9c', darkBg: '#452d38' }
  ];
  var LS_KEY = 'mysite_accent';

  function isDark() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function applyAccent(t) {
    var r = document.documentElement.style;
    // --pink / --pink-bg 本体不再内联改写:亮色下经 --accent-* 桥接,
    // 暗色下写各主题的暗色版(明暗切换由下面的观察器负责重刷)
    r.setProperty('--accent-pink', isDark() ? t.darkPink : t.pink);
    r.setProperty('--accent-pink-bg', isDark() ? t.darkBg : t.bg);
    r.setProperty('--pink-shadow', isDark() ? t.darkBg : t.shadow);
    r.setProperty('--hl', t.hl);
  }

  function initAccent() {
    // 站长在后台固定了主题色 → 前台锁死,不显示切换按钮(预留 data-accent-locked)
    var locked = document.documentElement.getAttribute('data-accent-locked');
    var saved = null;
    try { saved = localStorage.getItem(LS_KEY); } catch (e) { }

    var current = THEMES[0];
    if (locked) {
      current = THEMES.find(function (t) { return t.key === locked; }) || THEMES[0];
      applyAccent(current);
      return;                       // 锁定时完全不给切
    }
    var hasSaved = saved && THEMES.some(function (t) { return t.key === saved; });
    if (hasSaved) {
      current = THEMES.find(function (t) { return t.key === saved; });
      applyAccent(current);
    }
    // 无论有没有保存过,按钮都给(首次访问也能换色)
    var btn = document.createElement('button');
    btn.className = 'accent-btn';
    btn.setAttribute('aria-label', '换个主题色');
    btn.title = '换个主题色 🎨';
    btn.innerHTML = '🎨';

    var panel = document.createElement('div');
    panel.className = 'accent-panel';
    panel.innerHTML = THEMES.map(function (t) {
      return '<button class="accent-opt' + (t.key === current.key ? ' on' : '') +
        '" data-k="' + t.key + '" title="' + t.name + '" style="background:' +
        t.pink + '"></button>';
    }).join('') +
      '<button class="accent-opt accent-reset" data-k="__reset" title="恢复默认 🍬" ' +
      'style="background:linear-gradient(135deg,#ff6b9d,#ffd93d)">↺</button>';

    btn.addEventListener('click', function (ev) {
      ev.stopPropagation();
      panel.classList.toggle('open');
    });
    panel.addEventListener('click', function (ev) {
      var k = ev.target.getAttribute && ev.target.getAttribute('data-k');
      if (!k) return;
      var reset = (k === '__reset');
      var t = reset ? THEMES[0] : THEMES.find(function (x) { return x.key === k; });
      if (!t) return;
      if (reset) {
        try { localStorage.removeItem(LS_KEY); } catch (e) { }
      } else {
        try { localStorage.setItem(LS_KEY, k); } catch (e) { }
      }
      applyAccent(t);
      panel.querySelectorAll('.accent-opt').forEach(function (el) {
        el.classList.toggle('on', el.getAttribute('data-k') === (reset ? 'candy' : k));
      });
      btn.animate([{ transform: 'rotate(0) scale(1)' },
                   { transform: 'rotate(20deg) scale(1.25)' },
                   { transform: 'rotate(0) scale(1)' }], { duration: 350 });
    });
    document.addEventListener('click', function (ev) {
      if (!panel.contains(ev.target) && ev.target !== btn) panel.classList.remove('open');
    });

    // 明暗切换时重刷 accent(亮/暗版色值不同,内联的要跟着换)。
    // theme.js 在明暗实际变化时广播 themechange 事件;兜底轮询防漏
    var _lastDark = isDark();
    document.addEventListener('themechange', function (e) {
      _lastDark = !!e.detail.dark;
      applyAccent(current);
    });
    setInterval(function () {
      var d = isDark();
      if (d !== _lastDark) {
        _lastDark = d;
        applyAccent(current);
      }
    }, 400);

    document.body.appendChild(btn);
    document.body.appendChild(panel);
  }

  /* ===================== 时间问候 ===================== */
  function initGreeting() {
    document.querySelectorAll('.hero .role').forEach(function (el) {
      var h = new Date().getHours();
      var greet, emoji;
      if (h < 5)       { greet = '夜深了'; emoji = '🌙'; }
      else if (h < 9)  { greet = '早上好'; emoji = '☀️'; }
      else if (h < 12) { greet = '上午好'; emoji = '🌤️'; }
      else if (h < 14) { greet = '中午好'; emoji = '🍚'; }
      else if (h < 18) { greet = '下午好'; emoji = '☕'; }
      else if (h < 23) { greet = '晚上好'; emoji = '🌆'; }
      else             { greet = '夜深了'; emoji = '🌙'; }

      var em = document.createElement('span');
      em.className = 'greet-emoji';
      em.textContent = emoji + ' ';
      var span = document.createElement('span');
      span.className = 'greet-line';
      span.textContent = greet + '!';
      el.insertBefore(span, el.firstChild);
      el.insertBefore(em, el.firstChild);
    });
  }

  function boot() {
    initAccent();
    initGreeting();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
