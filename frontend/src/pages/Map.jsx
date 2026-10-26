import React, { useEffect } from 'react';

/** 来访地图 页(骨架,待填充) */
export default function MapPage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '来访地图 · 至尊杰的小窝',
      description: '来访地图',
      canonical: 'https://imyxj.xyz/' + ('map' === 'home' ? '' : 'map' + '.html'),
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head">
      <div className="container">
        <h2>来访地图</h2>
        <p className="hint">内容迁移中…</p>
      </div>
    </section>
  );
}
