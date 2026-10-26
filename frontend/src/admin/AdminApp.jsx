import React, { useState } from 'react';

/**
 * 后台外壳(阶段一):先接管侧边栏导航 + 面板切换,
 * 各面板内容仍由现有 DOM 承载,后续逐步替换成 React 组件。
 */
const PANELS = [
  { id: 'skills', label: '技能树', group: '内容管理' },
  { id: 'timeline', label: '校园日常', group: '内容管理' },
  { id: 'stats', label: '趣味统计', group: '内容管理' },
  { id: 'works', label: '项目墙', group: '内容管理' },
  { id: 'honors', label: '荣誉墙', group: '内容管理' },
  { id: 'notes', label: '随手记', group: '内容管理' },
  { id: 'friendlinks', label: '友情链接', group: '内容管理' },
  { id: 'songs', label: '音乐', group: '内容管理' },
  { id: 'messages', label: '留言板', group: '内容管理' },
  { id: 'questions', label: '提问箱', group: '内容管理' },
  { id: 'doodles', label: '涂鸦墙', group: '内容管理' },
  { id: 'site-info', label: '站点信息', group: '个人信息' },
  { id: 'profile-about', label: '自我介绍', group: '个人信息' },
  { id: 'profile-info', label: '信息卡片', group: '个人信息' },
  { id: 'uploads', label: '图片库', group: '媒体资源' },
  { id: 'gallery', label: '相册', group: '媒体资源' },
  { id: 'dashboard', label: '数据看板', group: '站点维护' },
  { id: 'fx', label: '前台特效', group: '站点维护' },
  { id: 'notices', label: '站点公告', group: '站点维护' },
  { id: 'countdown', label: '倒计时', group: '站点维护' },
  { id: 'backup', label: '数据备份', group: '站点维护' },
  { id: 'likes', label: '点赞统计', group: '站点维护' },
  { id: 'sec-pass', label: '后台密码', group: '安全中心' },
  { id: 'sec-login', label: '登录防护', group: '安全中心' },
  { id: 'sec-blocked', label: '封锁名单', group: '安全中心' },
  { id: 'sec-sessions', label: '登录会话', group: '安全中心' },
  { id: 'sec-audit', label: '操作记录', group: '安全中心' },
  { id: 'sec-status', label: '防护状态', group: '安全中心' },
];

const GROUPS = ['内容管理', '个人信息', '媒体资源', '站点维护', '安全中心'];

export default function AdminApp({ initialData }) {
  const [active, setActive] = useState('skills');
  const [collapsed, setCollapsed] = useState({});

  const byGroup = (g) => PANELS.filter((p) => p.group === g);

  return (
    <div className="admin-react-shell">
      <aside className="admin-react-sidebar">
        <div className="admin-react-brand">🏠 我的小窝</div>
        {GROUPS.map((g) => (
          <div key={g} className="admin-react-group">
            <button
              className="admin-react-group-btn"
              onClick={() => setCollapsed((s) => ({ ...s, [g]: !s[g] }))}
              aria-expanded={!collapsed[g]}
            >
              {g}
            </button>
            {!collapsed[g] && (
              <ul className="admin-react-list">
                {byGroup(g).map((p) => (
                  <li key={p.id}>
                    <button
                      className={`admin-react-link${active === p.id ? ' active' : ''}`}
                      onClick={() => setActive(p.id)}
                    >
                      {p.label}
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ))}
      </aside>
      <main className="admin-react-main">
        <p className="hint">React 后台迁移中,当前面板:{active}</p>
      </main>
    </div>
  );
}
