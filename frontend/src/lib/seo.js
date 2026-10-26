/**
 * SEO / 文档头管理:React 单页切换时同步 title、description、canonical、og 标签。
 * 服务端仍会渲染首屏 meta(保证爬虫拿到内容),这里只做客户端跳转后的更新。
 */

function setMeta(attr, key, value) {
  if (!value) return;
  let el = document.head.querySelector(`meta[${attr}="${key}"]`);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute('content', value);
}

function setLink(rel, href) {
  if (!href) return;
  let el = document.head.querySelector(`link[rel="${rel}"]`);
  if (!el) {
    el = document.createElement('link');
    el.setAttribute('rel', rel);
    document.head.appendChild(el);
  }
  el.setAttribute('href', href);
}

export function applySeo({ title, description, canonical, ogTitle, ogDescription }) {
  if (title) document.title = title;
  setMeta('name', 'description', description);
  setMeta('property', 'og:title', ogTitle || title);
  setMeta('property', 'og:description', ogDescription || description);
  setLink('canonical', canonical);
}
