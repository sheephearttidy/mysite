/**
 * SpotlightCard —— 光标跟随的聚光灯卡片。
 * 对应 React Bits 的 Spotlight Card:光斑位置用 CSS 变量驱动,
 * 只在 hover 时更新,离开后淡出。
 */
import { useRef, type ReactNode } from 'react';
import clsx from 'clsx';

interface SpotlightCardProps {
  children: ReactNode;
  className?: string;
  /** 光斑半径(px) */
  size?: number;
  /** 光斑颜色 */
  color?: string;
}

export function SpotlightCard({
  children,
  className,
  size = 260,
  color = 'rgba(255, 217, 61, 0.28)',
}: SpotlightCardProps) {
  const ref = useRef<HTMLDivElement>(null);

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    el.style.setProperty('--mx', `${e.clientX - rect.left}px`);
    el.style.setProperty('--my', `${e.clientY - rect.top}px`);
  };

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      className={clsx('group relative overflow-hidden', className)}
      style={
        {
          '--spot-size': `${size}px`,
          '--spot-color': color,
        } as React.CSSProperties
      }
    >
      {/* 聚光层:默认透明,hover 时显现 */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            'radial-gradient(var(--spot-size) circle at var(--mx, 50%) var(--my, 50%), var(--spot-color), transparent 70%)',
        }}
      />
      <div className="relative">{children}</div>
    </div>
  );
}
