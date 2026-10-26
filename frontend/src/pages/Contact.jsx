import React, { useEffect } from 'react';

/** 来找我玩 页(骨架,待填充) */
export default function ContactPage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '来找我玩 · 至尊杰的小窝',
      description: '来找我玩',
      canonical: 'https://imyxj.xyz/' + ('contact' === 'home' ? '' : 'contact' + '.html'),
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head">
      <div className="container">
        <h2>来找我玩</h2>
        <p className="hint">内容迁移中…</p>
      </div>
    </section>
  );
}
