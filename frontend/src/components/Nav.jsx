import React, { useEffect, useState } from 'react';
import BranchedMenu from './BranchedMenu.jsx';
import { PAGES, navigate } from '../lib/router.js';
import { HugeiconsIcon } from '@hugeicons/react';
import {
  Home01Icon,
  UserIcon,
  StarIcon,
  Folder01Icon,
  Calendar03Icon,
  Image01Icon,
  MapsLocation01Icon,
  Mail01Icon,
  Menu01Icon,
  Settings02Icon,
  PaintBoardIcon,
  BookOpen01Icon,
} from '@hugeicons/core-free-icons';

/* 页面 → 图标 */
const MENU_ICONS = {
  index: Home01Icon,
  about: UserIcon,
  skills: StarIcon,
  works: Folder01Icon,
  campus: Calendar03Icon,
  gallery: Image01Icon,
  map: MapsLocation01Icon,
  contact: Mail01Icon,
};

/**
 * 全站多级导航(v4.2.0)
 *
 * 桌面端:左侧常驻的分支式菜单(BranchedMenu),多级分组 + 折叠。
 * 移动端:同一份菜单收进抽屉,点汉堡展开。
 * 两端共用 MENU_ITEMS,不重复维护。
 */
const MENU_ITEMS = [
  {
    label: '浏览',
    children: [
      { value: 'index', label: '首页', icon: MENU_ICONS.index },
      { value: 'works', label: '小破项目', icon: MENU_ICONS.works },
      { value: 'gallery', label: '相册', icon: MENU_ICONS.gallery },
      { value: 'campus', label: '校园日常', icon: MENU_ICONS.campus },
    ],
  },
  {
    label: '了解我',
    children: [
      { value: 'about', label: '关于我', icon: MENU_ICONS.about },
      { value: 'skills', label: '技能树', icon: MENU_ICONS.skills },
      { value: 'map', label: '来访地图', icon: MENU_ICONS.map },
      { value: 'contact', label: '来找我玩', icon: MENU_ICONS.contact },
    ],
  },
  {
    label: '更多',
    children: [
      { value: 'docs', label: 'API 文档', icon: BookOpen01Icon },
      { value: 'admin', label: '后台管理', icon: Settings02Icon },
    ],
  },
];

/* 不属于 PAGES 的额外跳转目标 */
const EXTRA_ROUTES = {
  docs: '/docs/api.html',
  admin: '/admin/',
};

export default function Nav({ pageId }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [theme, setTheme] = useState(
    () => document.documentElement.getAttribute('data-theme') || 'light'
  );

  useEffect(() => {
    document.body.style.overflow = drawerOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [drawerOpen]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (e) => { if (e.key === 'Escape') setDrawerOpen(false); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [drawerOpen]);

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    document.documentElement.setAttribute('data-theme', next);
    document.documentElement.setAttribute('data-theme-source', 'manual');
    try { localStorage.setItem('theme', next); } catch { /* 隐私模式 */ }
  };

  const handleSelect = (value) => {
    setDrawerOpen(false);
    if (EXTRA_ROUTES[value]) {
      window.location.href = EXTRA_ROUTES[value];
      return;
    }
    const p = PAGES.find((x) => x.id === value);
    if (p) navigate(p.path);
  };

  const menuCommon = {
    items: MENU_ITEMS,
    defaultOpen: [0, 1],
    defaultActive: pageId,
    onSelect: handleSelect,
    width: 210,
    rowHeight: 36,
    indent: 38,
    trunk: 12,
    radius: 9,
    lineWidth: 1.5,
    fontSize: 13.5,
    drawDuration: 380,
    foldDuration: 280,
  };

  return (
    <>
      {/* 顶栏:logo + 桌面端菜单按钮 + 主题切换 */}
      <header className="nav">
        <div className="container nav-inner">
          <a
            href="/"
            className="logo"
            onClick={(e) => { e.preventDefault(); handleSelect('index'); }}
          >
            <span className="dot" />
            <span data-site="site_name">至尊杰的小窝</span>
          </a>

          <div className="nav-actions">
            <button
              className="nav-menu-btn"
              aria-label="打开导航菜单"
              aria-expanded={drawerOpen}
              onClick={() => setDrawerOpen(true)}
            >
              <HugeiconsIcon icon={Menu01Icon} size={20} strokeWidth={2.4} />
              <span>菜单</span>
            </button>
            <button
              className="theme-toggle"
              onClick={toggleTheme}
              aria-label="切换深色模式"
              title="切换深色模式"
            >
              <span className="ti-sun">☀️</span>
              <span className="ti-moon">🌙</span>
            </button>
          </div>
        </div>
      </header>

      {/* 抽屉:桌面端从左侧滑出,移动端从右侧。共用 BranchedMenu */}
      {drawerOpen && (
        <div
          className="drawer-scrim"
          onClick={() => setDrawerOpen(false)}
          aria-hidden="true"
        />
      )}
      <aside
        className={`drawer${drawerOpen ? ' open' : ''}`}
        aria-hidden={!drawerOpen}
        aria-label="站点导航"
      >
        <div className="drawer-head">
          <span className="drawer-title">导航</span>
          <button
            className="drawer-close"
            onClick={() => setDrawerOpen(false)}
            aria-label="关闭菜单"
          >
            ✕
          </button>
        </div>
        <div className="drawer-body">
          <BranchedMenu
            {...menuCommon}
            key={pageId}
            color="var(--ink, #2d2a32)"
            accentColor="var(--pink, #ff6b9d)"
            lineColor="rgba(0,0,0,.22)"
          />
        </div>
      </aside>
    </>
  );
}
