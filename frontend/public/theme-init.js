/**
 * 主题初始化:在首屏绘制前同步执行,避免深色用户看到白屏闪一下。
 *
 * 独立成文件(而非内联)是为了配合严格 CSP(script-src 'self'),
 * 内联脚本会被 CSP 拦掉,导致防闪烁失效。
 */
(function () {
  try {
    var saved = localStorage.getItem('theme');
    var dark = saved
      ? saved === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches;
    if (dark) document.documentElement.setAttribute('data-theme', 'dark');
  } catch (e) {
    /* localStorage 不可用时忽略 */
  }
})();
