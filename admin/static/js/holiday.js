/* ============================================================
   节日特效:按日期给 <html> 打 data-holiday 标记
   前后台共用;必须在 body 内容渲染前执行(放 head,theme.js 之前)
   用法:holiday.js 检测 -> CSS 里 [data-holiday="national-day"] 生效
   ============================================================ */

(function () {
  try {
    var now = new Date();
    // 用本地时区拼 YYYY-MM-DD(避免 toISOString 的 UTC 偏移)
    var m = now.getMonth() + 1;   // 1-12
    var d = now.getDate();        // 1-31
    var key = '';
    var label = '';

    // 公祭日要最先判断(优先级最高:任何节日撞上公祭日都黑白)
    if (m === 12 && d === 13) {
      key = 'memorial'; label = '国家公祭日';
    }
    // 国庆:10.1-10.7 红旗飘飘
    else if (m === 10 && d >= 1 && d <= 7) {
      key = 'national-day'; label = '国庆节';
    }
    // 情人节:2.14 爱心粒子
    else if (m === 2 && d === 14) {
      key = 'valentine'; label = '情人节';
    }
    // 元旦:1.1-1.2 烟花彩带
    else if (m === 1 && d <= 2) {
      key = 'new-year'; label = '元旦';
    }
    // 圣诞:12.24-12.25 雪花
    else if (m === 12 && (d === 24 || d === 25)) {
      key = 'christmas'; label = '圣诞节';
    }
    // 劳动节:5.1-5.5
    else if (m === 5 && d >= 1 && d <= 5) {
      key = 'labor'; label = '劳动节';
    }
    // 儿童节:6.1(强行装嫩)
    else if (m === 6 && d === 1) {
      key = 'children'; label = '儿童节';
    }
    // 教师节:9.10
    else if (m === 9 && d === 10) {
      key = 'teacher'; label = '教师节';
    }

    if (key) {
      document.documentElement.setAttribute('data-holiday', key);
      // 供 JS 特效读取
      document.documentElement.setAttribute('data-holiday-label', label);
    }
  } catch (e) { /* 检测失败就不过节,不影响页面 */ }
})();
