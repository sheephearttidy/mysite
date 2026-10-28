/**
 * Meteors —— 流星划过背景。
 * 对应 React Bits 的 Meteors:斜向下落的短光带。
 */
import { useMemo } from 'react';
import clsx from 'clsx';

interface MeteorsProps {
  className?: string;
  /** 流星数量 */
  number?: number;
  /** 颜色 */
  color?: string;
}

export function Meteors({ className, number = 14, color = 'var(--pink)' }: MeteorsProps) {
  // 位置与延迟固定下来,避免每次渲染都跳
  const meteors = useMemo(
    () =>
      Array.from({ length: number }, (_, i) => ({
        left: `${Math.random() * 100}%`,
        delay: `${(Math.random() * 6).toFixed(2)}s`,
        duration: `${(2.5 + Math.random() * 3).toFixed(2)}s`,
        key: i,
      })),
    [number],
  );

  return (
    <div
      aria-hidden
      className={clsx('pointer-events-none absolute inset-0 overflow-hidden', className)}
    >
      {meteors.map((m) => (
        <span
          key={m.key}
          className="absolute h-0.5 w-16 rounded-full"
          style={{
            left: m.left,
            top: '-8px',
            background: `linear-gradient(90deg, transparent, ${color})`,
            boxShadow: `0 0 8px ${color}`,
            animation: `meteor-fall ${m.duration} linear ${m.delay} infinite`,
          }}
        />
      ))}
      <style>{`
        @keyframes meteor-fall {
          0%   { transform: translate3d(0, 0, 0) rotate(35deg); opacity: 0; }
          10%  { opacity: 1; }
          70%  { opacity: 1; }
          100% { transform: translate3d(-260px, 460px, 0) rotate(35deg); opacity: 0; }
        }
        @media (prefers-reduced-motion: reduce) {
          span { animation: none !important; opacity: 0 !important; }
        }
      `}</style>
    </div>
  );
}
