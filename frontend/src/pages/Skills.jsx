import React, { useEffect } from 'react';

/** 技能树 页(骨架,待填充) */
export default function SkillsPage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '技能树 · 至尊杰的小窝',
      description: '技能树',
      canonical: 'https://imyxj.xyz/' + ('skills' === 'home' ? '' : 'skills' + '.html'),
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head">
      <div className="container">
        <h2>技能树</h2>
        <p className="hint">内容迁移中…</p>
      </div>
    </section>
  );
}
