/* ============================================================
   节日粒子特效:按 data-holiday 生成对应的装饰元素
   纯 DOM + CSS 动画,零依赖;body 加载完再执行
   ============================================================ */

(function () {
  try {
    var html = document.documentElement;
    var key = html.getAttribute('data-holiday');
    if (!key) return;
    // 后台登录页(没有 .container 结构)也显示,但后台管理页不刷屏
    var fx = document.createElement('div');
    fx.className = 'holiday-fx';
    document.body.appendChild(fx);

    var DEFS = {
      'national-day': { cls: 'flag', n: 16, emoji: '' },
      'valentine': { cls: 'heart', n: 18, emoji: '💗' },
      'memorial': { cls: 'candle', n: 6, emoji: '' },
      'new-year': { cls: 'streamer', n: 24, emoji: '' },
      'christmas': { cls: 'snowflake', n: 26, emoji: '❄️' },
      'labor': { cls: 'streamer', n: 18, emoji: '' },
      'children': { cls: 'plane', n: 8, emoji: '✈️' },
      'teacher': { cls: 'teacher-star', n: 20, emoji: '⭐' },
    };
    var def = DEFS[key];
    if (!def) return;

    var COLORS = ['#ff6b9d', '#ffb84d', '#7ec8b8', '#9aa7ff', '#ffd93d', '#8fd460'];
    var FIXED = { 'flag': '#de2910' };  // 国旗固定红色,其余用随机莫兰迪色
    var c = 0;
    for (var i = 0; i < def.n; i++) {
      var el = document.createElement('span');
      el.className = def.cls;
      if (def.emoji) el.textContent = def.emoji;
      // 随机横坐标 / 大小 / 时长 / 延迟
      el.style.left = (Math.random() * 100).toFixed(1) + '%';
      var scale = 0.7 + Math.random() * 0.9;
      el.style.fontSize = (14 * scale).toFixed(1) + 'px';
      el.style.animationDuration = (6 + Math.random() * 8).toFixed(1) + 's';
      el.style.animationDelay = (Math.random() * 6).toFixed(1) + 's';
      // 非 emoji 粒子给底色:旗固定红色,其余随机
      if (!def.emoji) el.style.background = FIXED[def.cls] || COLORS[c++ % COLORS.length];
      fx.appendChild(el);
    }
  } catch (e) { /* 特效失败不影响页面 */ }
})();
