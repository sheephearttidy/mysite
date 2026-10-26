import React, { useEffect } from 'react';

/** 相册 页(骨架,待填充) */
export default function GalleryPage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '相册 · 至尊杰的小窝',
      description: '相册',
      canonical: 'https://imyxj.xyz/' + ('gallery' === 'home' ? '' : 'gallery' + '.html'),
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head">
      <div className="container">
        <h2>相册</h2>
        <p className="hint">内容迁移中…</p>
      </div>
    </section>
  );
}
