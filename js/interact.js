/* ============================================================
   v1.9.0 互动包:留言墙 + 点赞 + 点击粒子 + 标签页标题彩蛋 + 页脚豆芽彩蛋
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
  // esc 用 core.js 的全局版本(v2.1 去掉本地副本)

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

    /* v2.7.0:访客凭证,只有原留言人能继续追问 */
    var TOK_KEY = 'mysite_msg_tokens';
    function getTokens() {
      try { return JSON.parse(localStorage.getItem(TOK_KEY) || '{}') || {}; }
      catch (e) { return {}; }
    }
    function setToken(id, tk) {
      try {
        var all = getTokens();
        all[id] = tk;
        localStorage.setItem(TOK_KEY, JSON.stringify(all));
      } catch (e) { }
    }
    function hasToken(id) { return !!getTokens()[id]; }

    function threadHtml(threads) {
      if (!threads || !threads.length) return '';
      var out = '';
      threads.forEach(function (t) {
        var owner = t.role === 'owner';
        out += '<div class="msg-turn ' + (owner ? 'owner' : 'guest') + '">' +
          '<span class="turn-who">' + (owner ? '站主' : '留言人') + '</span>' +
          '<span class="turn-text">' + esc(t.body) + '</span></div>';
      });
      return '<div class="msg-thread">' + out + '</div>';
    }

    function render(list) {
      grid.innerHTML = '';
      emptyEl.hidden = list.length > 0;
      if (!list.length) return;
      list.forEach(function (m, i) {
        var card = document.createElement('div');
        // v2.0.2 修复:此前 i=0 时 classList.add('') 抛异常导致整墙渲染崩溃
        card.className = 'msg-note msg-' + (m.color || 'pink');
        // v2.7.2:按内容量决定便签松紧,短句紧凑、长文略收字号
        var total = (m.body || '').length;
        (m.threads || []).forEach(function (t) { total += (t.body || '').length; });
        if (total <= 24) card.classList.add('msg-short');
        else if (total >= 120) card.classList.add('msg-long');
        if (i < 3) card.classList.add('reveal');
        if (i === 1) card.classList.add('d1');
        if (i === 2) card.classList.add('d2');
        card.innerHTML =
          '<div class="msg-head"><b class="msg-name">' + esc(m.name) + '</b>' +
          '<span class="msg-time">' + fmtTime(m.ts) + '</span></div>' +
          '<div class="msg-body-text">' + esc(m.body) + '</div>' +
          threadHtml(m.threads) +
          (hasToken(m.id)
            ? '<button class="msg-follow-btn" type="button">💬 继续追问</button>' +
              '<div class="msg-follow-box" hidden>' +
              '<textarea class="sf-input" rows="2" maxlength="140" ' +
              'placeholder="追问一句(140 字内,审核后显示)"></textarea>' +
              '<div class="msg-follow-foot"><span class="hint msg-follow-tip"></span>' +
              '<button class="btn msg-follow-send" type="button">发送</button></div></div>'
            : '');
        // 便签随机小角度,更像贴纸
        var rot = (Math.random() * 4 - 2).toFixed(2);
        card.style.setProperty('--rot', rot + 'deg');
        grid.appendChild(card);

        var fBtn = card.querySelector('.msg-follow-btn');
        if (fBtn) {
          var box = card.querySelector('.msg-follow-box');
          var ta = box.querySelector('textarea');
          var tip = box.querySelector('.msg-follow-tip');
          var sBtn = box.querySelector('.msg-follow-send');
          fBtn.addEventListener('click', function () {
            box.hidden = !box.hidden;
            if (!box.hidden) ta.focus();
          });
          sBtn.addEventListener('click', function () {
            var txt = (ta.value || '').trim();
            if (!txt) { tip.textContent = '写点什么呀~'; return; }
            sBtn.disabled = true;
            fetch('/api/messages/' + m.id + '/follow', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ body: txt, token: getTokens()[m.id] })
            }).then(function (r) { return r.json(); }).then(function (d) {
              if (d.ok) {
                ta.value = '';
                box.hidden = true;
                tip.textContent = '';
                if (typeof showToast === 'function') showToast('追问已提交,审核后显示');
              } else {
                tip.textContent = d.error || '发送失败';
              }
            }).catch(function () { tip.textContent = '网络开小差了'; })
              .finally(function () { sBtn.disabled = false; });
          });
        }
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
              if (r.d.token && r.d.id) setToken(r.d.id, r.d.token);
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

  /* ===================== 匿名提问箱(v2.8.0) ===================== */
  function initAskbox() {
    var box = document.getElementById('askbox');
    var bodyIn = document.getElementById('askBody');
    var countEl = document.getElementById('askCount');
    var sendBtn = document.getElementById('askSend');
    var tipEl = document.getElementById('askTip');
    var listEl = document.getElementById('qaList');
    if (!box || !bodyIn || !sendBtn) return;

    function tip(msg, warn) {
      tipEl.textContent = msg || '';
      tipEl.classList.toggle('warn', !!warn);
    }

    function fmtDate(ts) {
      try {
        var d = new Date(ts * 1000);
        return d.getFullYear() + '.' + ('0' + (d.getMonth() + 1)).slice(-2) + '.' +
               ('0' + d.getDate()).slice(-2);
      } catch (e) { return ''; }
    }

    function load() {
      fetch('/api/questions').then(function (r) { return r.json(); })
        .then(function (d) { render(d.questions || []); })
        .catch(function () { });
    }

    function render(list) {
      if (!listEl) return;
      if (!list.length) {
        listEl.innerHTML = '<p class="hint" style="text-align:center">还没有被翻牌的问题,来投第一个~</p>';
        return;
      }
      listEl.innerHTML = list.map(function (q) {
        return '<div class="qa-card card">' +
          '<div class="qa-q"><span class="qa-who">🫥 问</span><span class="qa-text">' + esc(q.body) + '</span></div>' +
          '<div class="qa-a"><span class="qa-who qa-me">🐳 答</span><span class="qa-text">' + esc(q.answer) + '</span></div>' +
          '<span class="qa-date">' + fmtDate(q.answered_ts) + '</span>' +
          '</div>';
      }).join('');
    }

    bodyIn.addEventListener('input', function () {
      countEl.textContent = bodyIn.value.length + ' / 200';
    });

    sendBtn.addEventListener('click', function () {
      var body = (bodyIn.value || '').trim();
      if (!body) { tip('先写点什么呀~ (期待脸)', true); bodyIn.focus(); return; }
      sendBtn.disabled = true;
      sendBtn.textContent = '投递中…';
      fetch('/api/questions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ body: body })
      }).then(function (r) { return r.json().then(function (d) { return { s: r.status, d: d }; }); })
        .then(function (r) {
          if (r.s === 200 && r.d.ok) {
            tip('投进去啦!被翻牌回答后会贴在下面 💌');
            bodyIn.value = '';
            countEl.textContent = '0 / 200';
          } else {
            tip(r.d.error || '投递失败,待会儿再试试', true);
          }
        })
        .catch(function () { tip('网络开小差了,再试一次?', true); })
        .finally(function () {
          sendBtn.disabled = false;
          sendBtn.textContent = '📮 投进提问箱';
        });
      setTimeout(function () { tip(''); }, 6000);
    });

    load();
  }

  /* ===================== 小彩蛋:浇灌页脚的 🌱 ===================== */
  // 连点 5 次(间隔超 1.6 秒清零)唤醒小鲸鱼;立绘首次触发才加载,平时零开销
  function initSproutEgg() {
    var sprout = document.querySelector('footer .sprout');
    var overlay = document.getElementById('eggOverlay');
    var closeBtn = document.getElementById('eggClose');
    if (!sprout || !overlay || !closeBtn) return;

    var clicks = 0, last = 0;

    sprout.addEventListener('click', function () {
      var now = Date.now();
      clicks = (now - last > 1600) ? 1 : clicks + 1;
      last = now;
      // 每次点都更用力地长一下
      sprout.style.setProperty('--pop', (1.3 + clicks * 0.3).toFixed(2));
      sprout.classList.remove('charged');
      void sprout.offsetWidth;               // 重置动画
      sprout.classList.add('charged');
      if (clicks < 5) return;
      clicks = 0;
      var img = document.getElementById('eggImg');
      // ?v= 是立绘的内容哈希:图片换新时重算,防浏览器/HTTP 7 天强缓存拿旧图
      if (img && !img.getAttribute('src')) img.src = '/assets/easter-whale.png?v=1b0f9cd7';
      overlay.classList.add('open');
      eggBubbles();
    });

    sprout.addEventListener('animationend', function () {
      sprout.classList.remove('charged');
    });

    function close() { overlay.classList.remove('open'); }
    closeBtn.addEventListener('click', close);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') close();
    });

    // 气泡从页面底部往上飘(尊重「动效总开关」)
    function eggBubbles() {
      if (document.documentElement.getAttribute('data-fx-off') === '1') return;
      for (var i = 0; i < 14; i++) {
        (function (i) {
          setTimeout(function () {
            var b = document.createElement('span');
            b.className = 'egg-bubble';
            b.textContent = Math.random() < 0.65 ? '🫧' : '✨';
            b.style.left = (5 + Math.random() * 90) + 'vw';
            b.style.fontSize = (13 + Math.random() * 17).toFixed(0) + 'px';
            b.style.animationDuration = (2.4 + Math.random() * 1.8).toFixed(2) + 's';
            document.body.appendChild(b);
            setTimeout(function () { b.remove(); }, 4400);
          }, i * 90);
        })(i);
      }
    }
  }

  /* ===================== 启动 ===================== */
  function boot() {
    initTitleEgg();
    initClickFx();
    initLikes();
    initMsgwall();
    initAskbox();
    initSproutEgg();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
