/**
 * 极简 hash-free 路由:用 History API 匹配现有 URL 结构
 * (/、/about.html、/gallery.html …),保持地址不变,SEO 不受影响。
 */

export const PAGES = [
  { id: 'index', path: '/', label: '首页' },
  { id: 'about', path: '/about.html', label: '关于我' },
  { id: 'skills', path: '/skills.html', label: '技能树' },
  { id: 'works', path: '/works.html', label: '小破项目' },
  { id: 'campus', path: '/campus.html', label: '校园日常' },
  { id: 'gallery', path: '/gallery.html', label: '相册' },
  { id: 'map', path: '/map.html', label: '来访地图' },
  { id: 'contact', path: '/contact.html', label: '来找我玩' },
];

/** 把当前 URL 映射成页面 id */
export function currentPageId() {
  const p = window.location.pathname.replace(/\/+$/, '') || '/';
  if (p === '/') return 'index';
  const hit = PAGES.find((x) => x.path === p);
  if (hit) return hit.id;
  const m = /^\/([a-z-]+)\.html$/.exec(p);
  return m ? m[1] : '404';
}

/** 编程式跳转(不刷新整页) */
export function navigate(path) {
  if (path === window.location.pathname) return;
  window.history.pushState({}, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
