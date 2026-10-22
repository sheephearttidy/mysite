/* ============================================================
   v1.9.0 互动包:留言墙 + 点赞 + 点击粒子 + 标签页标题彩蛋
   零依赖;每个功能独立小模块,互相不影响
   ============================================================ */

(function () {
  'use strict';

  /* ===================== 标签页标题彩蛋 ===================== */
  function initTitleEgg() {
    if (document.title.indexOf('至尊杰') === -1) return;   // 只在主站玩
    var base = document.title;
    var awayMsg = '别走嘛 (╥﹏╥)';
    var backMsg = '欢迎回来!🎉';
    var t = null;
    document.addEventListener('visibilitychange', function () {
      if (document.hidden) {
        document.title = awayMsg;
        if (t) clearTimeout(t);
      } else {
        document.title = backMsg;
        if (t) clearTimeout(t);
        t = setTimeout(function () { document.title = base; }, 2400);
      }
    });
  }

  /* ===================== 点击粒子 ===================== */
  function initClickFx() {
    // 管理后台不开启(免得刷屏);只在前台页面
    if (document.body.classList.contains('admin-body')) return;

    var COLORS = ['#ff6b9d', '#ffb84d', '#7ec8b8', '#9aa7ff', '#ffd93d', '#8fd460'];
    var EMOJIS = ['✨', '💖', '⭐', '🌸', '🍭'];

    // 尊重「动效总开关」:html[data-fx-off] 时跳过(由 fx 设置联动)
    if (document.documentElement.getAttribute('data-fx-off') === '1') return;

    document.addEventListener('click', function (ev) {
      // 点在表单控件上不炸,免得影响输入
      var tag = (ev.target.tagName || '').toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select' ||
          tag === 'button' || tag === 'a' || (ev.target.closest && ev.target.closest('a,button,input,textarea,select'))) return;

      var x = ev.clientX, y = ev.clientY;
      var emoji = EMOJIS[Math.floor(Math.random() * EMOJIS.length)];
      var color = COLORS[Math.floor(Math.random() * COLORS.length)];

      for (var i = 0; i < 8; i++) {
        var s = document.createElement('span');
        s.className = 'click-fx';
        s.textContent = Math.random() < 0.6 ? emoji : '●';
        if (s.textContent === '●') s.style.color = color;
        s.style.left = x + 'px';
        s.style.top = y + 'px';
        var ang = Math.random() * Math.PI * 2;
        var dist = 26 + Math.random() * 34;
        s.style.setProperty('--dx', (Math.cos(ang) * dist).toFixed(1) + 'px');
        s.style.setProperty('--dy', (Math.sin(ang) * dist - 18).toFixed(1) + 'px');
        s.style.animationDuration = (0.55 + Math.random() * 0.3).toFixed(2) + 's';
        document.body.appendChild(s);
        (function (el) { setTimeout(function () { el.remove(); }, 950); })(s);
      }
    }, { passive: true });
  }

  /* ===================== 点赞 ===================== */
  function pageKey() {
    var m = { 'index.html': 'home', '/': 'home' };
    var path = location.pathname.split('/').pop() || '/';
    if (path === '' || path === 'index.html') return 'home';
    return m[path] || path.replace('.html', '');
  }

  function initLikes() {
    var btn = document.getElementById('likeBtn');
    if (!btn) return;
    var page = pageKey();
    if (!['home', 'about', 'skills', 'works', 'campus', 'map', 'contact'].includes(page)) return;

    var KEY = 'mysite_liked_' + page;
    var liked = false;
    try { liked = localStorage.getItem(KEY) === '1'; } catch (e) { }

    function paint(n, isLiked) {
      var num = btn.querySelector('.like-n');
      if (num) num.textContent = n > 999 ? (n / 1000).toFixed(1) + 'k' : String(n);
      btn.classList.toggle('liked', !!isLiked);
    }

    fetch('/api/likes').then(function (r) { return r.json(); }).then(function (d) {
      paint((d.likes && d.likes[page]) || 0, liked);
    }).catch(function () { });

    if (liked) { btn.disabled = true; return; }

    btn.addEventListener('click', function () {
      if (liked) return;
      liked = true;
      btn.disabled = true;
      btn.classList.add('pop');
      try { localStorage.setItem(KEY, '1'); } catch (e) { }
      fetch('/api/likes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ page: page })
      }).then(function (r) { return r.json(); }).then(function (d) {
        paint(d.n || 0, true);
      }).catch(function () { });
    });
  }

  /* ===================== 留言墙 ===================== */
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  function fmtTime(ts) {
    try {
      var d = new Date(ts * 1000);
      var today = new Date();
      var sameDay = d.toDateString() === today.toDateString();
      var hm = ('0' + d.getHours()).slice(-2) + ':' + ('0' + d.getMinutes()).slice(-2);
      if (sameDay) return '今天 ' + hm;
      var yest = new Date(today.getTime() - 86400000);
      if (d.toDateString() === yest.toDateString()) return '昨天 ' + hm;
      return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + hm;
    } catch (e) { return ''; }
  }

  function initMsgwall() {
    var grid = document.getElementById('msgwallGrid');
    if (!grid) return;

    var nameIn = document.getElementById('msgName');
    var colorIn = document.getElementById('msgColor');
    var bodyIn = document.getElementById('msgBody');
    var countEl = document.getElementById('msgCount');
    var sendBtn = document.getElementById('msgSend');
    var tipEl = document.getElementById('msgTip');
    var emptyEl = document.getElementById('msgEmpty');

    function load() {
      fetch('/api/messages').then(function (r) { return r.json(); })
        .then(function (d) { render(d.messages || []); })
        .catch(function () { });
    }

    function render(list) {
      grid.innerHTML = '';
      emptyEl.hidden = list.length > 0;
      if (!list.length) return;
      list.forEach(function (m, i) {
        var card = document.createElement('div');
        // v2.0.2 修复:此前 i=0 时 classList.add('') 抛异常导致整墙渲染崩溃
        card.className = 'msg-note msg-' + (m.color || 'pink');
        if (i < 3) card.classList.add('reveal');
        if (i === 1) card.classList.add('d1');
        if (i === 2) card.classList.add('d2');
        var replyHtml = m.reply
          ? '<div class="msg-reply"><b>站主:</b>' + esc(m.reply) + '</div>' : '';
        card.innerHTML =
          '<div class="msg-head"><b class="msg-name">' + esc(m.name) + '</b>' +
          '<span class="msg-time">' + fmtTime(m.ts) + '</span></div>' +
          '<div class="msg-body-text">' + esc(m.body) + '</div>' + replyHtml;
        // 便签随机小角度,更像贴纸
        var rot = (Math.random() * 4 - 2).toFixed(2);
        card.style.setProperty('--rot', rot + 'deg');
        grid.appendChild(card);
      });
      // v2.0.2 修复:卡片是 fetch 后动态插入的,main.js 的滚动观察器
      // 只在页面加载时收集 .reveal,这些卡永远等不到 visible → 一直透明。
      // 自己观察一轮,进视口就显形
      if ('IntersectionObserver' in window) {
        var wallIO = new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) {
              e.target.classList.add('visible');
              wallIO.unobserve(e.target);
            }
          });
        }, { threshold: 0.12 });
        grid.querySelectorAll('.reveal').forEach(function (el) { wallIO.observe(el); });
      } else {
        grid.querySelectorAll('.reveal').forEach(function (el) {
          el.classList.add('visible');
        });
      }
    }

    if (bodyIn && countEl) {
      bodyIn.addEventListener('input', function () {
        countEl.textContent = bodyIn.value.length + ' / 140';
      });
    }

    if (sendBtn) {
      sendBtn.addEventListener('click', function () {
        var body = (bodyIn.value || '').trim();
        if (!body) {
          tipEl.textContent = '先写点什么嘛~ (期待脸)';
          tipEl.classList.add('warn');
          bodyIn.focus();
          return;
        }
        sendBtn.disabled = true;
        sendBtn.textContent = '发送中…';
        fetch('/api/messages', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: (nameIn.value || '').trim(),
            body: body,
            color: colorIn ? colorIn.value : ''
          })
        }).then(function (r) { return r.json().then(function (d) { return { s: r.status, d: d }; }); })
          .then(function (r) {
            if (r.s === 200 && r.d.ok) {
              tipEl.textContent = '贴上去啦!审核通过后就会出现在墙上 🎨';
              tipEl.classList.remove('warn');
              bodyIn.value = '';
              if (countEl) countEl.textContent = '0 / 140';
            } else {
              tipEl.textContent = r.d.error || '发送失败,待会儿再试试';
              tipEl.classList.add('warn');
            }
          })
          .catch(function () {
            tipEl.textContent = '网络开小差了,再试一次?';
            tipEl.classList.add('warn');
          })
          .finally(function () {
            sendBtn.disabled = false;
            sendBtn.textContent = '📮 贴到墙上';
          });
      });
    }

    load();
  }

  /* ===================== 启动 ===================== */
  function boot() {
    initTitleEgg();
    initClickFx();
    initLikes();
    initMsgwall();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
