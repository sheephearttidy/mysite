/**
 * 主题切换:手动选择 > 系统偏好,选择存 localStorage。
 * 切换时广播 themechange,供换肤等模块跟随明暗。
 */
import { useCallback, useEffect, useState } from 'react';

type Theme = 'light' | 'dark';

function resolveInitial(): Theme {
  try {
    const saved = localStorage.getItem('theme');
    if (saved === 'light' || saved === 'dark') return saved;
  } catch {
    /* localStorage 不可用时忽略 */
  }
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>(resolveInitial);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
    try {
      localStorage.setItem('theme', theme);
    } catch {
      /* 忽略 */
    }
    document.dispatchEvent(
      new CustomEvent('themechange', { detail: { dark: theme === 'dark' } }),
    );
  }, [theme]);

  // 未手动选择时跟随系统
  useEffect(() => {
    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = (e: MediaQueryListEvent) => {
      let saved: string | null = null;
      try {
        saved = localStorage.getItem('theme');
      } catch {
        /* 忽略 */
      }
      if (!saved) setThemeState(e.matches ? 'dark' : 'light');
    };
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);

  const toggle = useCallback(() => {
    setThemeState((t) => (t === 'dark' ? 'light' : 'dark'));
  }, []);

  return { theme, toggle, isDark: theme === 'dark' };
}
