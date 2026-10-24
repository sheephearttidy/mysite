/* ============================================================
   v3.1.0 小鲸鱼桌宠:不时从页面左下角探头陪访客
   - 后台「前台特效 → 🐳 小鲸鱼桌宠」开关(pet_mode)
   - 尊重动效总开关 data-fx-off=1:静默
   - 北京时间 0~5 点换深夜台词(深夜彩蛋)
   - 点她说话;小概率翻出完整彩蛋立绘(复用 eggOverlay)
   ============================================================ */
(function () {
  'use strict';

  var DAY_LINES = [
    '游过来看看你~',
    '今天也要开心哦 🐳',
    '水里凉快吧?',
    '偷偷告诉你:页脚有颗豆芽,连点五次…',
    '呼噜呼噜~',
    '带我兜兜风嘛'
  ];
  var NIGHT_LINES = [
    '这么晚还不睡?🐳',
    '深夜的水最深,早点休息~',
    '我再陪你一会儿,就一会儿'
  ];

  // 北京时间(UTC+8)的小时,和访客本地时区无关
  function bjHour() {
    var d = new Date(Date.now() + (new Date().getTimezoneOffset() + 480) * 60000);
    return d.getHours();
  }
  function pickLine(lastLine) {
    var pool = (bjHour() < 5) ? NIGHT_LINES : DAY_LINES;
    var s = pool[Math.floor(Math.random() * pool.length)];
    if (pool.length > 1 && s === lastLine) s = pickLine(lastLine);
    return s;
  }

  var whale = document.createElement('div');
  whale.className = 'pet-whale';
  whale.id = 'petWhale';
  whale.innerHTML =
    '<div class="pet-bubble" id="petBubble"></div>' +
    '<img src="/assets/easter-whale.png" alt="小鲸鱼" />';
  whale.setAttribute('role', 'button');
  whale.setAttribute('aria-label', '小鲸鱼');
  whale.title = '';

  var lastLine = '';
  var shown = 0;          // 本页累计出现次数
  var hideTimer = null;
  var timer = null;

  function say() {
    lastLine = pickLine(lastLine);
    whale.querySelector('.pet-bubble').textContent = lastLine;
  }

  function appear() {
    if (document.hidden) { timer = setTimeout(appear, 30000); return; }
    whale.classList.add('show');
    say();
    var stay = 8000 + Math.random() * 6000;
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hide, stay);
  }

  function hide() {
    whale.classList.remove('show');
    schedule();
  }

  function schedule(first) {
    if (shown >= 4) return;      // 单页最多 4 次,别烦人
    var delay = first ? (12000 + Math.random() * 18000)
                      : (180000 + Math.random() * 240000);
    timer = setTimeout(function () { shown++; appear(); }, delay);
  }

  whale.addEventListener('click', function () {
    say();
    // 小概率直接翻出完整彩蛋
    var egg = document.getElementById('eggOverlay');
    if (egg && Math.random() < 0.1 && !egg.classList.contains('open')) {
      var img = document.getElementById('eggImg');
      if (img && !img.getAttribute('src')) img.src = '/assets/easter-whale.png';
      egg.classList.add('open');
      hide();
      return;
    }
    // 点了就多待一会儿
    clearTimeout(hideTimer);
    hideTimer = setTimeout(hide, 8000);
  });

  // 动效总开关关掉时不出场(开关在 <html data-fx-off>)
  function fxOff() {
    return document.documentElement.getAttribute('data-fx-off') === '1';
  }

  // 读后台配置决定是否启用;拿不到配置时默认启用(别让彩蛋被网络抖动吃掉)
  fetch('/api/fx').then(function (r) { return r.json(); })
    .then(function (d) {
      if (d && d.pet === 'off') return;
      if (fxOff()) return;
      document.body.appendChild(whale);
      schedule(true);
    })
    .catch(function () {
      if (fxOff()) return;
      document.body.appendChild(whale);
      schedule(true);
    });
})();
