/**
 * SplitText —— 文字按字符/单词拆分后依次入场。
 * 对应 React Bits 的 Split Text 组件,用 CSS 变量控制延迟,零依赖。
 */
import { useEffect, useRef, useState } from 'react';
import clsx from 'clsx';

interface SplitTextProps {
  text: string;
  className?: string;
  /** 按字符还是按单词拆分 */
  splitBy?: 'chars' | 'words';
  /** 每个片段之间的延迟(毫秒) */
  delay?: number;
  /** 动画时长(毫秒) */
  duration?: number;
  /** 是否在挂载时立即播放 */
  immediate?: boolean;
  /** 触发阈值(0~1),进入视口多少比例后播放 */
  threshold?: number;
}

export function SplitText({
  text,
  className,
  splitBy = 'chars',
  delay = 30,
  duration = 600,
  immediate = true,
  threshold = 0.2,
}: SplitTextProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const [play, setPlay] = useState(immediate);

  useEffect(() => {
    if (immediate) return;
    const el = ref.current;
    if (!el) return;

    // 尊重「减少动效」偏好:直接显示,不做入场
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setPlay(true);
      return;
    }

    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setPlay(true);
          io.disconnect();
        }
      },
      { threshold },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [immediate, threshold]);

  const parts = splitBy === 'chars' ? Array.from(text) : text.split(/(\s+)/);

  return (
    <span ref={ref} className={clsx('inline-block', className)} aria-label={text}>
      {parts.map((part, i) => (
        <span
          key={i}
          aria-hidden
          className="inline-block will-change-transform"
          style={{
            opacity: play ? 1 : 0,
            transform: play ? 'translateY(0) rotate(0)' : 'translateY(0.4em) rotate(6deg)',
            transition: `opacity ${duration}ms cubic-bezier(.22,.9,.3,1.05) ${i * delay}ms, transform ${duration}ms cubic-bezier(.22,.9,.3,1.05) ${i * delay}ms`,
            whiteSpace: part.trim() === '' ? 'pre' : undefined,
          }}
        >
          {part === ' ' ? '\u00A0' : part}
        </span>
      ))}
    </span>
  );
}
