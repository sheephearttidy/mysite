/**
 * 页脚 —— 版权行 + 友情入口 + 返回顶部。
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

interface FooterProps {
  owner: string;
  credit: string;
  startYear: string;
}

export function Footer({ owner, credit, startYear }: FooterProps) {
  const [showTop, setShowTop] = useState(false);

  useEffect(() => {
    const onScroll = () => setShowTop(window.scrollY > 600);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const year = new Date().getFullYear();
  const span = startYear && startYear !== String(year) ? `${startYear}–${year}` : String(year);

  return (
    <footer
      className="mt-16 border-t-[3px] py-8"
      style={{ borderColor: 'var(--shadow)', background: 'var(--paper)' }}
    >
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-3 px-5 text-center text-sm">
        <p style={{ color: 'var(--text-2)' }}>
          © {span} {owner} · {credit}
        </p>
        <p className="flex items-center gap-3" style={{ color: 'var(--text-3)' }}>
          <Link to="/contact" className="underline decoration-dotted">
            联系我
          </Link>
          <span aria-hidden>·</span>
          <Link to="/admin" className="underline decoration-dotted">
            后台
          </Link>
        </p>
      </div>

      {showTop && (
        <button
          type="button"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          aria-label="返回顶部"
          className="fixed bottom-6 right-6 z-30 rounded-full border-[3px] px-4 py-3 font-black shadow-sticker"
          style={{ borderColor: 'var(--shadow)', background: 'var(--yellow)', color: '#2d2a32' }}
        >
          ↑
        </button>
      )}
    </footer>
  );
}
