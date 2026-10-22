/* ============================================================
   v1.10 数据包:公告横幅 + 倒计时角标
   公告:顶部横幅,可手动关闭(本次会话不再弹)
   倒计时:右下角小挂件,显示「XX 还有 N 天」
   ============================================================ */

(function () {
  'use strict';

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
  }

  /* ===================== 公告横幅 ===================== */
  function initNotice() {
    fetch('/api/notices/active').then(r => r.json()).then(d => {
      const n = d.notice;
      if (!n || !n.body) return;
      // 本次会话关过同一条就不再弹
      let closed = 0;
      try { closed = Number(sessionStorage.getItem('notice_closed') || 0); } catch (e) { }
      if (closed === n.id) return;

      const bar = document.createElement('div');
      bar.className = 'notice-bar';
      bar.innerHTML =
        '<div class="nb-inner">' +
        '<span class="nb-ico">📢</span>' +
        '<span class="nb-body">' + esc(n.body) + '</span>' +
        '<button class="nb-close" aria-label="关闭公告">✕</button>' +
        '</div>';
      bar.querySelector('.nb-close').addEventListener('click', function () {
        bar.remove();
        try { sessionStorage.setItem('notice_closed', String(n.id)); } catch (e) { }
      });
      // v2.0.1:插到 sticky 导航前面,公告吸顶时与导航天然衔接;
      // 内部用 .container 对齐页面栅格,长文不再顶死屏幕两边
      var nav = document.querySelector('nav.nav');
      if (nav && nav.parentNode) {
        nav.parentNode.insertBefore(bar, nav);
      } else {
        document.body.insertBefore(bar, document.body.firstChild);
      }
    }).catch(() => { });
  }

  /* ===================== 倒计时挂件 ===================== */
  function initCountdown() {
    fetch('/api/countdowns/active').then(r => r.json()).then(d => {
      const c = d.countdown;
      if (!c || !c.target) return;
      // 目标日按北京时间零点算
      const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(c.target);
      if (!m) return;
      const target = new Date(+m[1], +m[2] - 1, +m[3], 0, 0, 0);
      const now = new Date();
      const diffMs = target - now;
      const dayMs = 86400000;
      let label, cls;

      if (diffMs > 0) {
        const days = Math.ceil(diffMs / dayMs);
        if (days > 365) {
          label = '还有 ' + (days / 365).toFixed(1) + ' 年';
        } else if (days > 30) {
          label = '还有 ' + Math.floor(days / 30) + ' 个月' +
            (days % 30 ? ' + ' + (days % 30) + ' 天' : '');
        } else {
          label = '还有 ' + days + ' 天';
        }
        cls = days <= 7 ? ' soon' : '';      // 一周内高亮
      } else {
        const past = Math.floor(-diffMs / dayMs) + 1;
        if (past <= 2) { label = '就是今天!'; cls = ' today'; }
        else if (past <= 30) { label = '过去 ' + past + ' 天'; cls = ' past'; }
        else return;                          // 过去太久,不显示
      }

      const box = document.createElement('div');
      box.className = 'cd-widget' + cls;
      box.title = '距离「' + c.title + '」';
      box.innerHTML =
        '<span class="cd-emoji">' + (c.emoji || '⏳') + '</span>' +
        '<span class="cd-title">' + esc(c.title) + '</span>' +
        '<b class="cd-days">' + label + '</b>';
      document.body.appendChild(box);
    }).catch(() => { });
  }

  function boot() { initNotice(); initCountdown(); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
