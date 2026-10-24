/* ============================================================
   v2.0 Service Worker:个人站轻量离线方案
   策略:
   - 页面(HTML): network-first(拿不到才回缓存),避免更新不及时
   - 静态资源(js/css/img/font): cache-first(带版本参数,内容不变)
   - API(/api/*): 完全不缓存,永远走网络
   版本号 CACHE_NAME 变更即自动清旧缓存
   ============================================================ */
const CACHE_NAME = 'mysite-v3.1.0';
const OFFLINE_URLS = [
  '/',
  '/about.html', '/skills.html', '/works.html',
  '/campus.html', '/map.html', '/contact.html', '/gallery.html',
  '/css/base.css', '/css/home.css', '/css/widgets.css',
  '/css/dark.css', '/css/holidays.css', '/css/responsive.css',
  '/js/holiday.js', '/js/theme.js', '/js/core.js', '/js/ambience.js',
  '/js/main.js', '/js/interact.js', '/js/site-extra.js', '/js/holiday-fx.js',
  '/js/gallery.js', '/js/pet.js', '/js/doodle.js',
  '/manifest.json'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE_NAME)
      .then(c => c.addAll(OFFLINE_URLS).catch(() => { }))  // 个别失败不挡安装
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
      )
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  if (e.request.method !== 'GET') return;
  if (url.origin !== location.origin) return;      // 外部资源不管
  if (url.pathname.startsWith('/api/')) return;    // API 永远走网络
  if (url.pathname.startsWith('/admin')) return;   // 后台不缓存

  // 页面:network-first
  if (e.request.mode === 'navigate' ||
      (url.pathname.endsWith('.html') || url.pathname === '/')) {
    e.respondWith(
      fetch(e.request)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE_NAME).then(c => c.put(e.request, copy));
          return res;
        })
        .catch(() => caches.match(e.request).then(m => m || caches.match('/')))
    );
    return;
  }

  // 静态资源:cache-first
  e.respondWith(
    caches.match(e.request).then(m => m || fetch(e.request).then(res => {
      const copy = res.clone();
      caches.open(CACHE_NAME).then(c => c.put(e.request, copy));
      return res;
    }))
  );
});
