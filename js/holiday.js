/* ============================================================
   节日特效:决定 <html> 上的 data-holiday 标记
   优先级:后台手动配置 > 按日期自动检测 > 不过节
   必须在 body 内容渲染前执行(放 head),否则会闪一下

   后台配置来自 /api/fx(公开只读):
     mode=auto    按日期自动
     mode=manual  用 key 指定的节日
     mode=off     全关
   fetch 是异步的,head 里等不了,所以用同步 XHR(超时 1.2s),
   后台挂了/慢了一律回退到「按日期自动」,绝不让页面卡住。
   ============================================================ */

(function () {
  var LABELS = {
    'national-day': '国庆节',
    'valentine': '情人节',
    'memorial': '国家公祭日',
    'new-year': '元旦',
    'christmas': '圣诞节',
    'labor': '劳动节',
    'children': '儿童节',
    'teacher': '教师节',
  };

  // ---- 1. 按日期自动检测 ----
  function detectByDate() {
    var now = new Date();
    var m = now.getMonth() + 1;
    var d = now.getDate();
    // 公祭日最先判断(优先级最高:撞上任何节日都黑白)
    if (m === 12 && d === 13) return 'memorial';
    if (m === 10 && d >= 1 && d <= 7) return 'national-day';
    if (m === 2 && d === 14) return 'valentine';
    if (m === 1 && d <= 2) return 'new-year';
    if (m === 12 && (d === 24 || d === 25)) return 'christmas';
    if (m === 5 && d >= 1 && d <= 5) return 'labor';
    if (m === 6 && d === 1) return 'children';
    if (m === 9 && d === 10) return 'teacher';
    return '';
  }

  // ---- 2. 读后台配置 ----
  // v2.7.4 性能:原来是同步 XHR(false),会阻塞 HTML 解析直到 /api/fx 返回,
  // 网络慢时首屏要干等。现在改成「先用日期本地判断立即上色,再异步校正」:
  //   1) 立即按日期打标记(0 网络,不闪白)
  //   2) 异步拉 /api/fx,若后台配了手动/关闭,再改标记
  // 后台配置通常和日期判断一致,所以视觉上几乎不会跳。
  function readConfigAsync(cb) {
    try {
      var xhr = new XMLHttpRequest();
      xhr.open('GET', '/api/fx', true);   // true = 异步,不阻塞
      xhr.timeout = 1200;
      xhr.onload = function () {
        if (xhr.status !== 200) return cb(null);
        try { cb(JSON.parse(xhr.responseText) || null); } catch (e) { cb(null); }
      };
      xhr.onerror = xhr.ontimeout = function () { cb(null); };
      xhr.send(null);
    } catch (e) { cb(null); }
  }

  function applyKey(key) {
    if (key) {
      document.documentElement.setAttribute('data-holiday', key);
      document.documentElement.setAttribute('data-holiday-label', LABELS[key] || key);
    } else {
      document.documentElement.removeAttribute('data-holiday');
      document.documentElement.removeAttribute('data-holiday-label');
    }
  }

  // 第一步:先按日期立刻上标记(不等待网络)
  try { applyKey(detectByDate()); } catch (e) { }

  // 第二步:异步读后台配置,有差异再覆盖
  readConfigAsync(function (cfg) {
    try {
      var key = '';
      var effectsOff = !!(cfg && String(cfg.effects) === '0');
      if (effectsOff) {
        key = '';
      } else if (cfg && cfg.mode === 'off') {
        key = '';
      } else if (cfg && cfg.mode === 'manual') {
        key = LABELS[cfg.key] ? cfg.key : '';
      } else {
        key = detectByDate();   // auto 或读不到配置
      }
      applyKey(key);
    } catch (e) { /* 任何异常都不过节,不影响页面 */ }
  });
})();
