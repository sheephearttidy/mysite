/* ============================================================
   我的小窝 · 后台登录页脚本(点击验证码换一张)
   验证码关闭时页面上没有对应元素,脚本会自动跳过。
   ============================================================ */
(function () {
  const box = document.getElementById('capBox');
  if (!box) return;   // 验证码关闭时页面上没有这个元素
    const img = document.getElementById('capImg');
    let n = 0;
    box.addEventListener('click', () => {
      // 加时间戳强制绕过浏览器缓存
      img.src = '/admin/captcha.svg?t=' + Date.now() + '-' + (++n);
      document.getElementById('captcha').value = '';
      document.getElementById('captcha').focus();
    });
    img.addEventListener('error', () => {
      box.innerHTML = '<div class="refresh" style="opacity:1">加载失败,点此重试</div>';
    });
})();
