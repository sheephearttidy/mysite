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
} from '@hugeicons/core-free-icons';

/* 桌面端顶部导航的分组(供移动端抽屉复用) */
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

/* 移动端抽屉:分「浏览」和「了解我」两组 */
const DRAWER_ITEMS = [
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
];

export default function Nav({ pageId }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [theme, setTheme] = useState(
    () => document.documentElement.getAttribute('data-theme') || 'light'
  );

  // 抽屉打开时锁定滚动
  useEffect(() => {
    document.body.style.overflow = drawerOpen ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [drawerOpen]);

  // Esc 关闭抽屉
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

  const go = (path) => {
    setDrawerOpen(false);
    navigate(path);
  };

  return (
    <>
      <nav className="nav">
        <div className="container nav-inner">
          <a
            href="/"
            className="logo"
            onClick={(e) => { e.preventDefault(); go('/'); }}
          >
            <span className="dot" />
            <span data-site="site_name">至尊杰的小窝</span>
          </a>

          <button
            className="nav-toggle"
            aria-label="打开菜单"
            aria-expanded={drawerOpen}
            onClick={() => setDrawerOpen(true)}
          >
            <HugeiconsIcon icon={Menu01Icon} size={22} strokeWidth={2.4} />
          </button>

          <ul className="nav-links">
            {PAGES.map((p) => (
              <li key={p.id}>
                <a
                  href={p.path}
                  className={pageId === p.id ? 'active' : ''}
                  onClick={(e) => { e.preventDefault(); go(p.path); }}
                >
                  {p.label}
                </a>
              </li>
            ))}
            <li>
              <button
                className="theme-toggle"
                onClick={toggleTheme}
                aria-label="切换深色模式"
                title="切换深色模式"
              >
                <span className="ti-sun">☀️</span>
                <span className="ti-moon">🌙</span>
              </button>
            </li>
          </ul>
        </div>
      </nav>

      {/* 移动端抽屉:用 BranchedMenu 做分支式导航 */}
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
            items={DRAWER_ITEMS}
            defaultOpen={[0, 1]}
            defaultActive={pageId}
            onSelect={(value) => {
              const p = PAGES.find((x) => x.id === value);
              if (p) go(p.path);
            }}
            key={pageId}
            color="var(--ink, #2d2a32)"
            accentColor="var(--pink, #ff6b9d)"
            lineColor="rgba(0,0,0,.22)"
            width={230}
            rowHeight={38}
            indent={38}
            trunk={12}
            radius={9}
            lineWidth={1.5}
            fontSize={14}
            drawDuration={360}
            foldDuration={260}
          />
        </div>
      </aside>
    </>
  );
}
