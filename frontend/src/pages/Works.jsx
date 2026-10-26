import React, { useEffect } from 'react';

/** 小破项目 页(骨架,待填充) */
export default function WorksPage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '小破项目 · 至尊杰的小窝',
      description: '小破项目',
      canonical: 'https://imyxj.xyz/' + ('works' === 'home' ? '' : 'works' + '.html'),
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head">
      <div className="container">
        <h2>小破项目</h2>
        <p className="hint">内容迁移中…</p>
      </div>
    </section>
  );
}
