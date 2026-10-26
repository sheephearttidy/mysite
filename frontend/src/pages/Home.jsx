import React, { useEffect } from 'react';

/** 首页 页(骨架,待填充) */
export default function HomePage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '首页 · 至尊杰的小窝',
      description: '首页',
      canonical: 'https://imyxj.xyz/' + ('home' === 'home' ? '' : 'home' + '.html'),
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head">
      <div className="container">
        <h2>首页</h2>
        <p className="hint">内容迁移中…</p>
      </div>
    </section>
  );
}
