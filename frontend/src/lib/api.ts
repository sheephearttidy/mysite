/**
 * API 客户端:统一错误处理 + 类型化响应。
 * 所有请求同域(/api),凭 cookie 维持登录态。
 */

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    credentials: 'same-origin',
    headers: init?.body ? { 'Content-Type': 'application/json' } : undefined,
    ...init,
  });

  if (!res.ok) {
    let message = `请求失败 (${res.status})`;
    try {
      const data = await res.json();
      message = data.error || data.detail || message;
      // Pydantic 校验错误是数组
      if (Array.isArray(data.detail)) {
        message = data.detail.map((d: { msg?: string }) => d.msg).join('; ');
      }
    } catch {
      /* 响应体不是 JSON,保留默认文案 */
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'POST', body: body ? JSON.stringify(body) : undefined }),
  put: <T>(path: string, body?: unknown) =>
    request<T>(path, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};

// ---------------- 类型 ----------------

export type ColorKey = 'pink' | 'yellow' | 'teal' | 'purple' | 'orange' | 'blue';

export interface SiteInfo {
  site_owner: string;
  site_name: string;
  site_school: string;
  site_major: string;
  site_grade: string;
  site_focus: string;
  site_slogan: string;
  site_credit: string;
  site_start_year: string;
}

export interface Skill {
  id: number;
  name: string;
  percent: number;
  note: string;
  category: 'serious' | 'passive';
  color: ColorKey;
  sort: number;
}

export interface TimelineItem {
  id: number;
  emoji: string;
  time_label: string;
  title: string;
  content: string;
  sort: number;
}

export interface Stat {
  id: number;
  emoji: string;
  number: number;
  unit: string;
  label: string;
  sort: number;
}

export interface Work {
  id: number;
  emoji: string;
  cover: ColorKey;
  title: string;
  desc: string;
  pill: string;
  link: string;
  sort: number;
}

export interface ProfileItem {
  id: number;
  kind: 'about' | 'info';
  emoji: string;
  label: string;
  value: string;
  sort: number;
}

export interface Honor {
  id: number;
  emoji: string;
  year: string;
  title: string;
  desc: string;
  level: 'national' | 'provincial' | 'school' | 'other';
  sort: number;
}

export interface Note {
  id: number;
  emoji: string;
  text: string;
  mood: ColorKey;
  ts: number;
  sort: number;
}

export interface FriendLink {
  id: number;
  name: string;
  url: string;
  emoji: string;
  desc: string;
  sort: number;
}

export interface Song {
  id: number;
  title: string;
  artist: string;
  emoji: string;
  song_id: string;
  note: string;
  sort: number;
}

export interface Photo {
  id: number;
  file: string;
  title: string;
  desc: string;
  category: string;
  shot_at: string;
  width: number;
  height: number;
  shown: number;
  sort: number;
  ts: number;
}

export interface Thread {
  id: number;
  role: 'owner' | 'guest';
  body: string;
  ts: number;
}

export interface Message {
  id: number;
  name: string;
  body: string;
  color: ColorKey;
  ts: number;
  reply: string;
  threads: Thread[];
}

export interface Question {
  id: number;
  body: string;
  ts: number;
  answer: string;
  answered_ts: number;
}

export interface OnThisDay {
  kind: 'note' | 'photo';
  years_ago: number;
  emoji?: string;
  text?: string;
  mood?: ColorKey;
  file?: string;
  title?: string;
}

export interface PageData {
  site: SiteInfo;
  stats?: Stat[];
  onthisday?: OnThisDay[];
  profile?: ProfileItem[];
  honors?: Honor[];
  songs?: Song[];
  skills?: Skill[];
  works?: Work[];
  timeline?: TimelineItem[];
  notes?: Note[];
  friendlinks?: FriendLink[];
}
