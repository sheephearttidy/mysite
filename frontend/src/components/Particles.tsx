/**
 * Particles —— 漂浮粒子背景。
 * 对应 React Bits 的 Particles:canvas 绘制缓慢上浮的光点,
 * 鼠标靠近有轻微排斥。纯 2D canvas,零依赖。
 */
import { useEffect, useRef } from 'react';
import clsx from 'clsx';

interface ParticlesProps {
  className?: string;
  /** 粒子数量(按面积自适应) */
  count?: number;
  /** 粒子颜色 */
  color?: string;
  /** 最大半径 */
  maxSize?: number;
  /** 上浮速度 */
  speed?: number;
  /** 是否响应鼠标 */
  interactive?: boolean;
}

interface Dot {
  x: number;
  y: number;
  r: number;
  vx: number;
  vy: number;
  alpha: number;
}

export function Particles({
  className,
  count = 60,
  color = '255, 107, 157',
  maxSize = 2.6,
  speed = 0.25,
  interactive = true,
}: ParticlesProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);
  const dotsRef = useRef<Dot[]>([]);
  const mouseRef = useRef<{ x: number; y: number } | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // 尊重减少动效:不启动动画
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = 0;
    let height = 0;
    let dpr = 1;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = Math.floor(width * dpr);
      canvas.height = Math.floor(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

      // 按面积决定粒子数,避免大屏稀疏 / 小屏拥挤
      const target = Math.round((count * (width * height)) / (1200 * 700));
      const n = Math.max(18, Math.min(count * 2, target));

      dotsRef.current = Array.from({ length: n }, () => ({
        x: Math.random() * width,
        y: Math.random() * height,
        r: 0.6 + Math.random() * maxSize,
        vx: (Math.random() - 0.5) * speed,
        vy: -speed * (0.4 + Math.random()),
        alpha: 0.25 + Math.random() * 0.55,
      }));
    };

    const onMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseRef.current = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    };
    const onLeave = () => {
      mouseRef.current = null;
    };

    const draw = () => {
      ctx.clearRect(0, 0, width, height);

      for (const d of dotsRef.current) {
        // 鼠标排斥:靠得越近推开越明显
        const m = mouseRef.current;
        if (interactive && m) {
          const dx = d.x - m.x;
          const dy = d.y - m.y;
          const dist2 = dx * dx + dy * dy;
          const R = 110;
          if (dist2 < R * R && dist2 > 0.01) {
            const dist = Math.sqrt(dist2);
            const force = (1 - dist / R) * 0.9;
            d.x += (dx / dist) * force;
            d.y += (dy / dist) * force;
          }
        }

        d.x += d.vx;
        d.y += d.vy;

        // 循环:出界后从底部/侧边回来
        if (d.y < -10) {
          d.y = height + 10;
          d.x = Math.random() * width;
        }
        if (d.x < -10) d.x = width + 10;
        if (d.x > width + 10) d.x = -10;

        ctx.beginPath();
        ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${color}, ${d.alpha})`;
        ctx.fill();
      }

      rafRef.current = requestAnimationFrame(draw);
    };

    resize();
    draw();

    const ro = new ResizeObserver(resize);
    ro.observe(canvas);
    if (interactive) {
      window.addEventListener('mousemove', onMove);
      canvas.addEventListener('mouseleave', onLeave);
    }

    return () => {
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      window.removeEventListener('mousemove', onMove);
      canvas.removeEventListener('mouseleave', onLeave);
    };
  }, [count, color, maxSize, speed, interactive]);

  return (
    <canvas
      ref={canvasRef}
      aria-hidden
      className={clsx('pointer-events-none absolute inset-0 h-full w-full', className)}
    />
  );
}
