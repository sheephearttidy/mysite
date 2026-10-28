/**
 * 404:贴纸风错误页。
 */
import { Link } from 'react-router-dom';
import { SplitText } from '@/components/SplitText';

export default function NotFound() {
  return (
    <main className="mx-auto flex min-h-[70vh] max-w-3xl flex-col items-center justify-center px-5 py-16 text-center">
      <div className="relative">
        <span className="font-round text-[7rem] font-black leading-none" style={{ color: 'var(--yellow)' }}>
          4
        </span>
        <span
          className="mx-1 inline-block font-round text-[6rem] font-black leading-none"
          style={{ color: 'var(--pink)', animation: 'spin 6s linear infinite' }}
        >
          🍩
        </span>
        <span className="font-round text-[7rem] font-black leading-none" style={{ color: 'var(--yellow)' }}>
          4
        </span>
      </div>

      <h1 className="mt-4 font-round text-2xl font-black">
        <SplitText text="这个页面跑丢了" delay={60} />
      </h1>
      <p className="mt-3 text-sm" style={{ color: 'var(--text-2)' }}>
        可能是我还没写,也可能是链接打错了。要不回首页看看?
      </p>

      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Link to="/" className="btn btn-accent">🏠 回首页</Link>
        <Link to="/works" className="btn">🛠️ 看项目</Link>
        <Link to="/contact" className="btn">✉️ 来找我</Link>
      </div>

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </main>
  );
}
