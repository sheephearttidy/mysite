/**
 * Aurora 背景 —— 柔光渐变缓慢流动。
 * 对应 React Bits 的 Aurora / Soft Aurora,用 CSS 渐变 + 位移动画实现,
 * 比 WebGL 版轻很多,移动端也不掉帧。
 */
import clsx from 'clsx';

interface AuroraProps {
  className?: string;
  /** 三团光的颜色 */
  colors?: [string, string, string];
  /** 整体不透明度 */
  opacity?: number;
}

export function Aurora({
  className,
  colors = ['#ff6b9d', '#ffd93d', '#4da3ff'],
  opacity = 0.35,
}: AuroraProps) {
  return (
    <div
      aria-hidden
      className={clsx('pointer-events-none absolute inset-0 overflow-hidden', className)}
      style={{ opacity }}
    >
      <div
        className="absolute -left-1/4 -top-1/3 h-[70vh] w-[70vw] rounded-full blur-[90px]"
        style={{
          background: `radial-gradient(circle, ${colors[0]}, transparent 65%)`,
          animation: 'aurora-drift-1 18s ease-in-out infinite alternate',
        }}
      />
      <div
        className="absolute -right-1/4 top-0 h-[60vh] w-[60vw] rounded-full blur-[100px]"
        style={{
          background: `radial-gradient(circle, ${colors[1]}, transparent 65%)`,
          animation: 'aurora-drift-2 22s ease-in-out infinite alternate',
        }}
      />
      <div
        className="absolute bottom-0 left-1/3 h-[55vh] w-[55vw] rounded-full blur-[110px]"
        style={{
          background: `radial-gradient(circle, ${colors[2]}, transparent 65%)`,
          animation: 'aurora-drift-3 26s ease-in-out infinite alternate',
        }}
      />
      <style>{`
        @keyframes aurora-drift-1 {
          from { transform: translate3d(0,0,0) scale(1); }
          to   { transform: translate3d(8vw,6vh,0) scale(1.15); }
        }
        @keyframes aurora-drift-2 {
          from { transform: translate3d(0,0,0) scale(1.1); }
          to   { transform: translate3d(-10vw,8vh,0) scale(0.95); }
        }
        @keyframes aurora-drift-3 {
          from { transform: translate3d(0,0,0) scale(0.95); }
          to   { transform: translate3d(6vw,-8vh,0) scale(1.2); }
        }
      `}</style>
    </div>
  );
}
