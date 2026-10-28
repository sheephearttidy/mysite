/**
 * GradientText —— 流动渐变文字。
 * 对应 React Bits 的 Gradient Text:渐变沿文字滑动,可配置速度与颜色。
 */
import clsx from 'clsx';

interface GradientTextProps {
  children: React.ReactNode;
  className?: string;
  /** 渐变色停 */
  colors?: string[];
  /** 一轮动画时长(秒) */
  duration?: number;
  /** 动画方向 */
  direction?: 'horizontal' | 'vertical' | 'diagonal';
}

export function GradientText({
  children,
  className,
  colors = ['#ff6b9d', '#ffd93d', '#4da3ff', '#9b6bff', '#ff6b9d'],
  duration = 6,
  direction = 'horizontal',
}: GradientTextProps) {
  const angle = direction === 'vertical' ? '180deg' : direction === 'diagonal' ? '135deg' : '90deg';

  return (
    <span
      className={clsx('inline-block bg-clip-text text-transparent', className)}
      style={{
        backgroundImage: `linear-gradient(${angle}, ${colors.join(', ')})`,
        backgroundSize: direction === 'vertical' ? '100% 300%' : '300% 100%',
        animation: `gradient-flow ${duration}s linear infinite`,
        WebkitBackgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
      }}
    >
      {children}
      <style>{`
        @keyframes gradient-flow {
          0%   { background-position: 0% 50%; }
          100% { background-position: 200% 50%; }
        }
        @media (prefers-reduced-motion: reduce) {
          span { animation: none !important; }
        }
      `}</style>
    </span>
  );
}
