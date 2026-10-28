/**
 * TextType —— 打字机效果,带闪烁光标。
 * 对应 React Bits 的 Text Type:逐字输入,可循环多句。
 */
import { useEffect, useRef, useState } from 'react';
import clsx from 'clsx';

interface TextTypeProps {
  /** 单句或轮播多句 */
  text: string | string[];
  className?: string;
  /** 每字间隔(毫秒) */
  speed?: number;
  /** 打完一句停留多久再删(毫秒) */
  pause?: number;
  /** 是否循环 */
  loop?: boolean;
  /** 光标字符 */
  cursor?: string;
}

export function TextType({
  text,
  className,
  speed = 90,
  pause = 1600,
  loop = true,
  cursor = '▍',
}: TextTypeProps) {
  const lines = Array.isArray(text) ? text : [text];
  const [lineIdx, setLineIdx] = useState(0);
  const [shown, setShown] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [showCursor, setShowCursor] = useState(true);
  const timer = useRef<number | undefined>(undefined);

  // 尊重减少动效:直接显示第一句
  useEffect(() => {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setShown(lines[0] ?? '');
      setShowCursor(false);
    }
  }, [lines]);

  useEffect(() => {
    const current = lines[lineIdx] ?? '';
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (reduced) return;

    if (!deleting && shown === current) {
      // 打完一句:停留,然后删除(或停止)
      if (!loop && lineIdx === lines.length - 1) {
        timer.current = window.setTimeout(() => setShowCursor(false), pause);
        return () => window.clearTimeout(timer.current);
      }
      timer.current = window.setTimeout(() => setDeleting(true), pause);
      return () => window.clearTimeout(timer.current);
    }

    if (deleting && shown === '') {
      // 删完:切下一句
      setDeleting(false);
      setLineIdx((i) => (i + 1) % lines.length);
      return undefined;
    }

    const next = deleting
      ? current.slice(0, Math.max(0, shown.length - 1))
      : current.slice(0, shown.length + 1);

    timer.current = window.setTimeout(
      () => setShown(next),
      deleting ? speed / 2 : speed,
    );
    return () => window.clearTimeout(timer.current);
  }, [shown, deleting, lineIdx, lines, speed, pause, loop]);

  return (
    <span className={clsx('inline', className)}>
      {shown}
      {showCursor && (
        <span
          aria-hidden
          style={{ animation: 'cursor-blink 1s step-end infinite', opacity: 0.7 }}
        >
          {cursor}
        </span>
      )}
      <style>{`
        @keyframes cursor-blink { 0%, 100% { opacity: 0.7; } 50% { opacity: 0; } }
      `}</style>
    </span>
  );
}
