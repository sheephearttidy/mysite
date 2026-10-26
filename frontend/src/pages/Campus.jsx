import React, { useEffect } from 'react';

/** 校园日常 页(骨架,待填充) */
export default function CampusPage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '校园日常 · 至尊杰的小窝',
      description: '校园日常',
      canonical: 'https://imyxj.xyz/' + ('campus' === 'home' ? '' : 'campus' + '.html'),
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head">
      <div className="container">
        <h2>校园日常</h2>
        <p className="hint">内容迁移中…</p>
      </div>
    </section>
  );
}
