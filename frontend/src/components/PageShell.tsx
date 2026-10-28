/**
 * 通用页面容器:统一标题、间距、入场动画。
 */
import type { ReactNode } from 'react';
import { SplitText } from './SplitText';

interface PageShellProps {
  title: string;
  subtitle?: string;
  emoji?: string;
  children: ReactNode;
  /** 标题右侧的额外内容(如刷新按钮) */
  actions?: ReactNode;
}

export function PageShell({ title, subtitle, emoji, children, actions }: PageShellProps) {
  return (
    <main className="mx-auto max-w-6xl px-5 py-10">
      <header className="mb-8 flex flex-wrap items-end gap-4">
        <div>
          <h1 className="font-round text-3xl font-black sm:text-4xl">
            {emoji && <span className="mr-2">{emoji}</span>}
            <SplitText text={title} splitBy="chars" delay={35} />
          </h1>
          {subtitle && (
            <p className="mt-2 text-sm" style={{ color: 'var(--text-2)' }}>
              {subtitle}
            </p>
          )}
        </div>
        {actions && <div className="ml-auto">{actions}</div>}
      </header>
      {children}
    </main>
  );
}

/** 加载骨架:避免内容跳动 */
export function Loading({ label = '加载中…' }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-16 justify-center" style={{ color: 'var(--text-3)' }}>
      <span
        className="inline-block h-5 w-5 animate-spin rounded-full border-[3px] border-t-transparent"
        style={{ borderColor: 'var(--rule)', borderTopColor: 'transparent' }}
      />
      {label}
    </div>
  );
}

/** 空态提示 */
export function Empty({ text = '这里还空着' }: { text?: string }) {
  return (
    <p className="py-12 text-center text-sm" style={{ color: 'var(--text-3)' }}>
      {text}
    </p>
  );
}

/** 错误提示 */
export function ErrorBox({ message }: { message: string }) {
  return (
    <div
      className="rounded-sticker border-[3px] p-4 text-sm font-bold"
      style={{ borderColor: 'var(--shadow)', background: 'var(--pink-bg)', color: 'var(--ink)' }}
    >
      ⚠️ {message}
    </div>
  );
}
