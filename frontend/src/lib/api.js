/**
 * 我的小窝 · 前台 API 客户端
 * 统一封装 fetch,处理错误与 JSON 解析。
 */

const BASE = '';

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    let detail = '';
    try {
      const j = await res.json();
      detail = j.error || '';
    } catch { /* 非 JSON 响应 */ }
    throw new Error(detail || `请求失败 (${res.status})`);
  }
  return res.json();
}

export const api = {
  page: (name) => request(`/api/page/${name}`),
  content: () => request('/api/content'),
  gallery: (category) =>
    request('/api/gallery' + (category ? `?category=${encodeURIComponent(category)}` : '')),
  messages: () => request('/api/messages'),
  postMessage: (data) => request('/api/messages', { method: 'POST', body: JSON.stringify(data) }),
  followMessage: (id, data) =>
    request(`/api/messages/${id}/follow`, { method: 'POST', body: JSON.stringify(data) }),
  likes: () => request('/api/likes'),
  postLike: (page) => request('/api/likes', { method: 'POST', body: JSON.stringify({ page }) }),
  questions: () => request('/api/questions'),
  postQuestion: (body) => request('/api/questions', { method: 'POST', body: JSON.stringify({ body }) }),
  doodles: () => request('/api/doodles'),
  notices: () => request('/api/notices/active'),
  countdowns: () => request('/api/countdowns/active'),
  map: () => request('/api/map'),
  fx: () => request('/api/fx'),
  track: (data) => request('/api/track', { method: 'POST', body: JSON.stringify(data) }),
};

export default api;
