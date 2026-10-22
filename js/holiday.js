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

  // ---- 2. 同步读后台配置(失败就返回 null,走自动) ----
  function readConfig() {
    try {
      var xhr = new XMLHttpRequest();
      xhr.open('GET', '/api/fx', false);   // false = 同步
      xhr.timeout = 1200;
      xhr.send(null);
      if (xhr.status !== 200) return null;
      var d = JSON.parse(xhr.responseText);
      return (d && typeof d === 'object') ? d : null;
    } catch (e) {
      return null;
    }
  }

  try {
    var cfg = readConfig();
    var key = '';
    var effectsOff = !!(cfg && String(cfg.effects) === '0');

    if (effectsOff) {
      key = '';                       // 动效总开关关掉:任何节日特效都不出现
    } else if (cfg && cfg.mode === 'off') {
      key = '';
    } else if (cfg && cfg.mode === 'manual') {
      key = LABELS[cfg.key] ? cfg.key : '';
    } else {
      key = detectByDate();   // auto 或读不到配置
    }

    if (key) {
      document.documentElement.setAttribute('data-holiday', key);
      document.documentElement.setAttribute('data-holiday-label', LABELS[key] || key);
    }
  } catch (e) { /* 任何异常都不过节,不影响页面 */ }
})();
