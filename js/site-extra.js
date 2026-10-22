/* ============================================================
   v1.10 数据包:公告横幅 + 倒计时角标
   公告:v2.0.2 起改为顶部居中弹窗(自动消失+可手动关),不再常驻顶部
   倒计时:右下角小挂件,显示「XX 还有 N 天」
   ============================================================ */

(function () {
  'use strict';

  // esc 用 core.js 的全局版本(v2.1 去掉本地副本)

  /* ===================== 公告弹窗 ===================== */
  function initNotice() {
    fetch('/api/notices/active').then(r => r.json()).then(d => {
      const n = d.notice;
      if (!n || !n.body) return;
      // 本次会话关过同一条就不再弹
      let closed = 0;
      try { closed = Number(sessionStorage.getItem('notice_closed') || 0); } catch (e) { }
      if (closed === n.id) return;

      const pop = document.createElement('div');
      pop.className = 'notice-pop';
      pop.setAttribute('role', 'alert');
      pop.innerHTML =
        '<span class="np-ico">📢</span>' +
        '<div class="np-text"><b class="np-tag">公告</b>' +
        '<span class="np-body">' + esc(n.body) + '</span></div>' +
        '<button class="np-close" aria-label="关闭公告">✕</button>';

      const kill = () => {
        pop.classList.remove('show');          // 触发退出动画
        try { sessionStorage.setItem('notice_closed', String(n.id)); } catch (e) { }
        setTimeout(() => pop.remove(), 260);
      };
      pop.querySelector('.np-close').addEventListener('click', kill);

      // 进场:下一帧加 .show 走过渡
      requestAnimationFrame(() => requestAnimationFrame(() => {
        pop.classList.add('show');
        // 已在页首(滚动了)则贴顶,否则给导航留出空间
        if (window.scrollY > 40) pop.classList.add('docked');
      }));

      // 自动消失:12 秒(手动关过也写会话标记)
      const timer = setTimeout(kill, 12000);
      pop.addEventListener('mouseenter', () => clearTimeout(timer)); // 悬停不消失

      // 滚动后贴顶
      const dock = () => pop.classList.toggle('docked', window.scrollY > 40);
      window.addEventListener('scroll', dock, { passive: true });

      document.body.appendChild(pop);
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
