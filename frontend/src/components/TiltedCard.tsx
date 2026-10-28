/**
 * TiltedCard —— 3D 倾斜卡片,跟随指针倾斜。
 * 对应 React Bits 的 Tilted Card,纯 transform 实现,无 WebGL。
 */
import { useRef, type ReactNode } from 'react';
import clsx from 'clsx';

interface TiltedCardProps {
  children: ReactNode;
  className?: string;
  /** 最大倾斜角度 */
  max?: number;
  /** 缩放 */
  scale?: number;
}

export function TiltedCard({ children, className, max = 8, scale = 1.02 }: TiltedCardProps) {
  const ref = useRef<HTMLDivElement>(null);

  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = ref.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const px = (e.clientX - rect.left) / rect.width - 0.5;
    const py = (e.clientY - rect.top) / rect.height - 0.5;
    el.style.transform = `perspective(800px) rotateX(${-py * max}deg) rotateY(${px * max}deg) scale(${scale})`;
  };

  const onLeave = () => {
    const el = ref.current;
    if (!el) return;
    el.style.transform = 'perspective(800px) rotateX(0) rotateY(0) scale(1)';
  };

  return (
    <div
      ref={ref}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
      className={clsx('transition-transform duration-200 ease-out will-change-transform', className)}
    >
      {children}
    </div>
  );
}
