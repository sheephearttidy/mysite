/* ============================================================
   主题切换(前台 + 后台共用同一个文件)
   优先级:localStorage 里的手动选择 > 系统偏好
   没手动选过就一直跟着系统走,系统切换时页面实时跟着变

   按钮 id 前台叫 themeToggle,后台叫 themeBtn,两个都认。
   ============================================================ */
(function () {
  'use strict';

  var mq = window.matchMedia('(prefers-color-scheme: dark)');

  function stored() {
    try { return localStorage.getItem('theme'); } catch (e) { return null; }
  }
  function systemMode() { return mq.matches ? 'dark' : 'light'; }
  function findBtn() {
    return document.getElementById('themeToggle') || document.getElementById('themeBtn');
  }

  function paint(mode) {
    var isDark = mode === 'dark';
    var root = document.documentElement;

    var wasDark = root.getAttribute('data-theme') === 'dark';
    if (isDark) root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');

    // v3.2.1:明暗实际变化时广播事件(ambience.js 换肤要跟着换暗色版色值)
    if (wasDark !== isDark) {
      document.dispatchEvent(new CustomEvent('themechange', { detail: { dark: isDark } }));
    }

    var manual = stored();
    root.setAttribute('data-theme-source', manual ? 'manual' : 'system');

    // 按钮提示同步成「点了会变成什么」
    var btn = findBtn();
    if (btn) {
      var label = isDark ? '切换到浅色模式' : '切换到深色模式';
      btn.setAttribute('aria-label', label);
      btn.title = manual ? label : label + '(当前跟随系统)';
    }

    // 手机状态栏颜色
    var metas = document.querySelectorAll('meta[name="theme-color"]');
    for (var i = 0; i < metas.length; i++) {
      metas[i].setAttribute('content', isDark ? '#1c1a21' : '#fff8ee');
    }
  }

  // 初始:有手动选择就用手动的,否则跟随系统
  paint(stored() || systemMode());

  // 系统偏好变化:只有没手动锁定过才跟随
  if (mq.addEventListener) {
    mq.addEventListener('change', function (e) {
      if (!stored()) paint(e.matches ? 'dark' : 'light');
    });
  } else if (mq.addListener) {
    mq.addListener(function (e) {   // 老 Safari
      if (!stored()) paint(e.matches ? 'dark' : 'light');
    });
  }

  // 手动切换
  var btn = findBtn();
  if (btn) {
    btn.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme') === 'dark'
        ? 'dark' : 'light';
      var next = cur === 'dark' ? 'light' : 'dark';
      paint(next);
      try { localStorage.setItem('theme', next); } catch (e) {}
    });
  }
})();
