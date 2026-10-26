import React, { useEffect, useState } from 'react';

/** 页脚:版权 + 返回顶部 + 微信二维码弹窗 */
export default function Footer() {
  const [showTop, setShowTop] = useState(false);
  const [qrOpen, setQrOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setShowTop(window.scrollY > 400);
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <>
      <footer>
        <div className="container">
          <p>
            <span className="sprout">🌱</span>{' '}
            © 2026 至尊杰 · 燕京理工学院 · 纯手搓 + AI 协作 · learning and building
          </p>
        </div>
      </footer>

      <button
        className={`back-top${showTop ? ' show' : ''}`}
        onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
        aria-label="返回顶部"
      >
        🚀
      </button>

      <button className="qr-fab" onClick={() => setQrOpen(true)} aria-label="微信二维码">
        💬
      </button>

      {qrOpen && (
        <div className="qr-modal" onClick={() => setQrOpen(false)}>
          <div className="qr-box" onClick={(e) => e.stopPropagation()}>
            <button className="qr-close" onClick={() => setQrOpen(false)} aria-label="关闭">✕</button>
            <img src="/assets/wechat-qr.jpg" alt="微信二维码" />
            <p className="hint">微信扫一扫,加个好友吧 🎉</p>
          </div>
        </div>
      )}
    </>
  );
}
