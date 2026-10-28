/**
 * 顶部导航 —— 粘性、移动端抽屉、当前页高亮。
 */
import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import clsx from 'clsx';
import { useTheme } from '@/lib/theme';

export const NAV_ITEMS = [
  { to: '/', label: '首页', emoji: '🏠' },
  { to: '/about', label: '关于我', emoji: '🧍' },
  { to: '/skills', label: '技能树', emoji: '🎯' },
  { to: '/works', label: '项目墙', emoji: '🛠️' },
  { to: '/campus', label: '校园日常', emoji: '🗺️' },
  { to: '/gallery', label: '相册', emoji: '📷' },
  { to: '/map', label: '来访地图', emoji: '🌍' },
  { to: '/contact', label: '来找我', emoji: '✉️' },
];

export function Nav({ siteName }: { siteName: string }) {
  const { pathname } = useLocation();
  const { isDark, toggle } = useTheme();
  const [open, setOpen] = useState(false);

  // 路由变化时自动收起抽屉
  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  // 抽屉打开时锁滚动
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : '';
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  return (
    <>
      <header
        className="sticky top-0 z-40 border-b-[3px] backdrop-blur-md"
        style={{ borderColor: 'var(--shadow)', background: 'color-mix(in srgb, var(--cream) 88%, transparent)' }}
      >
        <nav className="mx-auto flex max-w-6xl items-center gap-3 px-5 py-3">
          <Link
            to="/"
            className="font-round text-lg font-black tracking-tight"
            style={{ color: 'var(--ink)' }}
          >
            🏠 {siteName}
          </Link>

          {/* 桌面端导航 */}
          <ul className="ml-auto hidden items-center gap-1 lg:flex">
            {NAV_ITEMS.map((item) => {
              const active = pathname === item.to;
              return (
                <li key={item.to}>
                  <Link
                    to={item.to}
                    className={clsx(
                      'rounded-full px-3 py-1.5 text-sm font-bold transition-colors',
                      active ? 'shadow-sticker-sm' : 'hover:opacity-70',
                    )}
                    style={{
                      background: active ? 'var(--yellow)' : 'transparent',
                      color: active ? '#2d2a32' : 'var(--ink)',
                      border: active ? '2px solid var(--shadow)' : '2px solid transparent',
                    }}
                  >
                    {item.label}
                  </Link>
                </li>
              );
            })}
          </ul>

          <button
            type="button"
            onClick={toggle}
            aria-label={isDark ? '切换到亮色模式' : '切换到暗色模式'}
            className="ml-auto rounded-full border-2 px-3 py-1.5 text-sm lg:ml-2"
            style={{ borderColor: 'var(--shadow)', background: 'var(--paper)' }}
          >
            {isDark ? '☀️' : '🌙'}
          </button>

          {/* 移动端汉堡 */}
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            aria-label="打开菜单"
            aria-expanded={open}
            className="rounded-full border-2 px-3 py-1.5 text-sm lg:hidden"
            style={{ borderColor: 'var(--shadow)', background: 'var(--paper)' }}
          >
            {open ? '✕' : '☰'}
          </button>
        </nav>
      </header>

      {/* 移动端抽屉 */}
      {open && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/45"
            onClick={() => setOpen(false)}
            aria-hidden
          />
          <aside
            className="absolute right-0 top-0 flex h-full w-[min(300px,84vw)] flex-col border-l-[3px]"
            style={{ borderColor: 'var(--shadow)', background: 'var(--cream)' }}
          >
            <div
              className="flex items-center justify-between border-b-2 px-4 py-3"
              style={{ borderColor: 'var(--rule)' }}
            >
              <span className="font-round font-black">菜单</span>
              <button type="button" onClick={() => setOpen(false)} aria-label="关闭菜单">
                ✕
              </button>
            </div>
            <ul className="flex-1 overflow-y-auto p-3">
              {NAV_ITEMS.map((item) => (
                <li key={item.to}>
                  <Link
                    to={item.to}
                    className="flex items-center gap-3 rounded-xl px-3 py-2.5 font-bold"
                    style={{
                      background: pathname === item.to ? 'var(--yellow)' : 'transparent',
                      color: pathname === item.to ? '#2d2a32' : 'var(--ink)',
                    }}
                  >
                    <span>{item.emoji}</span>
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </aside>
        </div>
      )}
    </>
  );
}
