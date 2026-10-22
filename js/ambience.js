/* ============================================================
   v1.9.1 氛围包:主题色换肤 + 时间问候
   与 theme.js 的暗色系统独立共存(换品牌色,不动明暗)
   ============================================================ */

(function () {
  'use strict';

  /* ===================== 主题色换肤 ===================== */
  /* 六套预设品牌色:覆盖 --pink / --pink-bg / --pink-shadow / --hl */
  var THEMES = [
    { key: 'candy',  name: '🍬 奶糖粉', pink: '#ff6b9d', bg: '#ffe4ef', shadow: '#c94f76', hl: 'rgba(255, 217, 61, 0.95)' },
    { key: 'mint',   name: '🌿 薄荷绿', pink: '#2fa886', bg: '#e0f4ee', shadow: '#1f7d64', hl: 'rgba(120, 220, 190, 0.5)' },
    { key: 'sky',    name: '☁️ 天空蓝', pink: '#4a90d9', bg: '#e2edf9', shadow: '#2f6dad', hl: 'rgba(140, 195, 250, 0.5)' },
    { key: 'grape',  name: '🍇 葡萄紫', pink: '#8b6bd9', bg: '#ebe5f9', shadow: '#6a4cb5', hl: 'rgba(190, 170, 245, 0.5)' },
    { key: 'honey',  name: '🍯 蜂蜜橙', pink: '#e88a3a', bg: '#fdeede', shadow: '#b56722', hl: 'rgba(250, 205, 140, 0.55)' },
    { key: 'sakura', name: '🌸 樱花木', pink: '#c96b85', bg: '#f9e4ea', shadow: '#a34a66', hl: 'rgba(240, 180, 200, 0.55)' }
  ];
  var LS_KEY = 'mysite_accent';

  function applyAccent(t) {
    var r = document.documentElement.style;
    r.setProperty('--pink', t.pink);
    r.setProperty('--pink-bg', t.bg);
    r.setProperty('--pink-shadow', t.shadow);
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
    }).join('');

    btn.addEventListener('click', function (ev) {
      ev.stopPropagation();
      panel.classList.toggle('open');
    });
    panel.addEventListener('click', function (ev) {
      var k = ev.target.getAttribute && ev.target.getAttribute('data-k');
      if (!k) return;
      var t = THEMES.find(function (x) { return x.key === k; });
      applyAccent(t);
      try { localStorage.setItem(LS_KEY, k); } catch (e) { }
      panel.querySelectorAll('.accent-opt').forEach(function (el) {
        el.classList.toggle('on', el.getAttribute('data-k') === k);
      });
      btn.animate([{ transform: 'rotate(0) scale(1)' },
                   { transform: 'rotate(20deg) scale(1.25)' },
                   { transform: 'rotate(0) scale(1)' }], { duration: 350 });
    });
    document.addEventListener('click', function (ev) {
      if (!panel.contains(ev.target) && ev.target !== btn) panel.classList.remove('open');
    });

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
