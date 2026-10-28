/**
 * GridBackground —— 网格底纹 + 光标聚光。
 * 对应 React Bits 的 Grid Scan / Cursor Grid:网格随光标照亮一块区域。
 */
import { useEffect, useRef } from 'react';
import clsx from 'clsx';

interface GridBackgroundProps {
  className?: string;
  /** 网格尺寸(px) */
  size?: number;
  /** 网格线颜色 */
  lineColor?: string;
  /** 聚光半径 */
  spotSize?: number;
}

export function GridBackground({
  className,
  size = 44,
  lineColor = 'var(--rule)',
  spotSize = 260,
}: GridBackgroundProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const onMove = (e: MouseEvent) => {
      const rect = el.getBoundingClientRect();
      el.style.setProperty('--gx', `${e.clientX - rect.left}px`);
      el.style.setProperty('--gy', `${e.clientY - rect.top}px`);
    };
    window.addEventListener('mousemove', onMove);
    return () => window.removeEventListener('mousemove', onMove);
  }, []);

  return (
    <div
      ref={ref}
      aria-hidden
      className={clsx('pointer-events-none absolute inset-0 overflow-hidden', className)}
      style={
        {
          '--grid-size': `${size}px`,
          '--spot': `${spotSize}px`,
          backgroundImage: `linear-gradient(${lineColor} 1px, transparent 1px),
                            linear-gradient(90deg, ${lineColor} 1px, transparent 1px)`,
          backgroundSize: 'var(--grid-size) var(--grid-size)',
          maskImage:
            'radial-gradient(var(--spot) circle at var(--gx, 50%) var(--gy, 50%), #000 0%, transparent 75%)',
          WebkitMaskImage:
            'radial-gradient(var(--spot) circle at var(--gx, 50%) var(--gy, 50%), #000 0%, transparent 75%)',
          opacity: 0.55,
        } as React.CSSProperties
      }
    />
  );
}
