/**
 * ShinyText —— 高光扫过文字。
 * 对应 React Bits 的 Shiny Text:一道亮带周期性掠过。
 */
import clsx from 'clsx';

interface ShinyTextProps {
  children: React.ReactNode;
  className?: string;
  /** 一次扫过时长(秒) */
  duration?: number;
  /** 高光颜色 */
  shineColor?: string;
  /** 是否禁用 */
  disabled?: boolean;
}

export function ShinyText({
  children,
  className,
  duration = 4,
  shineColor = 'rgba(255,255,255,0.9)',
  disabled = false,
}: ShinyTextProps) {
  return (
    <span
      className={clsx('inline-block bg-clip-text text-transparent', className)}
      style={{
        backgroundImage: disabled
          ? 'none'
          : `linear-gradient(110deg, var(--ink) 35%, ${shineColor} 50%, var(--ink) 65%)`,
        backgroundSize: '250% 100%',
        animation: disabled ? undefined : `shiny-sweep ${duration}s linear infinite`,
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        color: disabled ? 'var(--ink)' : undefined,
      }}
    >
      {children}
      <style>{`
        @keyframes shiny-sweep {
          0%   { background-position: 150% 50%; }
          100% { background-position: -50% 50%; }
        }
      `}</style>
    </span>
  );
}
