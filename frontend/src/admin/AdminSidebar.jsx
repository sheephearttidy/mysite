import React, { useState } from 'react';
import BranchedMenu from '../components/BranchedMenu.jsx';
import {
  StarIcon,
  Calendar03Icon,
  Chart01Icon,
  Folder01Icon,
  Trophy,
  Note01Icon,
  Link01Icon,
  MusicNote01Icon,
  Message01Icon,
  HelpCircleIcon,
  BrushIcon,
  Tag01Icon,
  UserIcon,
  Card,
  Image01Icon,
  Camera01Icon,
  Analytics01Icon,
  SparklesIcon,
  Megaphone01Icon,
  Timer01Icon,
  Database01Icon,
  FavouriteIcon,
  Key01Icon,
  Shield01Icon,
  BlockedIcon,
  ComputerIcon,
  File01Icon,
  SecurityCheckIcon,
} from '@hugeicons/core-free-icons';

/** 后台 27 个面板按 5 组归类 */
export const ADMIN_MENU = [
  {
    label: '内容管理',
    children: [
      { value: 'skills', label: '技能树', icon: StarIcon },
      { value: 'timeline', label: '校园日常', icon: Calendar03Icon },
      { value: 'stats', label: '趣味统计', icon: Chart01Icon },
      { value: 'works', label: '项目墙', icon: Folder01Icon },
      { value: 'honors', label: '荣誉墙', icon: Trophy },
      { value: 'notes', label: '随手记', icon: Note01Icon },
      { value: 'friendlinks', label: '友情链接', icon: Link01Icon },
      { value: 'songs', label: '音乐', icon: MusicNote01Icon },
      { value: 'messages', label: '留言板', icon: Message01Icon },
      { value: 'questions', label: '提问箱', icon: HelpCircleIcon },
      { value: 'doodles', label: '涂鸦墙', icon: BrushIcon },
    ],
  },
  {
    label: '个人信息',
    children: [
      { value: 'site-info', label: '站点信息', icon: Tag01Icon },
      { value: 'profile-about', label: '自我介绍', icon: UserIcon },
      { value: 'profile-info', label: '信息卡片', icon: Card },
    ],
  },
  {
    label: '媒体资源',
    children: [
      { value: 'uploads', label: '图片库', icon: Image01Icon },
      { value: 'gallery', label: '相册', icon: Camera01Icon },
    ],
  },
  {
    label: '站点维护',
    children: [
      { value: 'dashboard', label: '数据看板', icon: Analytics01Icon },
      { value: 'fx', label: '前台特效', icon: SparklesIcon },
      { value: 'notices', label: '站点公告', icon: Megaphone01Icon },
      { value: 'countdown', label: '倒计时', icon: Timer01Icon },
      { value: 'backup', label: '数据备份', icon: Database01Icon },
      { value: 'likes', label: '点赞统计', icon: FavouriteIcon },
    ],
  },
  {
    label: '安全中心',
    children: [
      { value: 'sec-pass', label: '后台密码', icon: Key01Icon },
      { value: 'sec-login', label: '登录防护', icon: Shield01Icon },
      { value: 'sec-blocked', label: '封锁名单', icon: BlockedIcon },
      { value: 'sec-sessions', label: '登录会话', icon: ComputerIcon },
      { value: 'sec-audit', label: '操作记录', icon: File01Icon },
      { value: 'sec-status', label: '防护状态', icon: SecurityCheckIcon },
    ],
  },
];

/** 找到某面板属于哪一组(用于初始展开) */
function groupIndexOf(panelId) {
  return ADMIN_MENU.findIndex((g) => g.children?.some((c) => c.value === panelId));
}

export default function AdminSidebar({ initialPanel, onNavigate }) {
  const [active, setActive] = useState(initialPanel || 'skills');
  const [dark, setDark] = useState(
    () => document.documentElement.getAttribute('data-theme') === 'dark'
  );

  const toggleTheme = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.setAttribute('data-theme', next ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme-source', 'manual');
    try { localStorage.setItem('theme', next ? 'dark' : 'light'); } catch { /* noop */ }
  };

  const gi = groupIndexOf(active);

  return (
    <>
      <div className="admin-react-brand">
        🏠 我的小窝
        <span className="admin-react-sub">后台管理</span>
      </div>

      <BranchedMenu
        items={ADMIN_MENU}
        defaultOpen={gi >= 0 ? [gi] : [0]}
        defaultActive={active}
        onSelect={(value) => {
          setActive(value);
          onNavigate?.(value);
        }}
        color="var(--ink, #2d2a32)"
        accentColor="var(--pink, #ff6b9d)"
        lineColor="rgba(0,0,0,.22)"
        width={196}
        rowHeight={31}
        indent={32}
        trunk={10}
        radius={8}
        lineWidth={1.4}
        fontSize={12.5}
        drawDuration={320}
        foldDuration={240}
      />

      <div className="admin-react-foot">
        <button className="admin-react-theme" onClick={toggleTheme}>
          {dark ? '☀️ 浅色' : '🌙 深色'}
        </button>
        <a className="admin-react-link-out" href="/" target="_blank" rel="noopener">
          👀 看看主页
        </a>
        <a className="admin-react-link-out" href="/admin/logout">🚪 退出登录</a>
      </div>
    </>
  );
}
