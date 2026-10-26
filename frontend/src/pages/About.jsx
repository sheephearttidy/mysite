import React, { useEffect } from 'react';

/** 关于我 页(骨架,待填充) */
export default function AboutPage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '关于我 · 至尊杰的小窝',
      description: '关于我',
      canonical: 'https://imyxj.xyz/' + ('about' === 'home' ? '' : 'about' + '.html'),
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head">
      <div className="container">
        <h2>关于我</h2>
        <p className="hint">内容迁移中…</p>
      </div>
    </section>
  );
}
