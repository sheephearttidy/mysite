import React, { useEffect } from 'react';

/** 404 页 */
export default function NotFoundPage({ onSeo }) {
  useEffect(() => {
    onSeo?.({
      title: '页面走丢了 · 至尊杰的小窝',
      description: '这个页面走丢了。',
    });
  }, [onSeo]);

  return (
    <section className="sec-cream page-head err-page">
      <div className="container">
        <div className="err-card">
          <div className="err-code" aria-hidden="true">
            <span className="err-digit">4</span>
            <span className="err-zero">🍩</span>
            <span className="err-digit">4</span>
          </div>
          <h2>这个页面走丢了<span className="wave-hand"> 🧭</span></h2>
          <p className="err-text">
            你要找的页面好像不在这儿 —— 可能是链接打错了,<br />
            也可能它被我搬走或者删掉了。
          </p>
          <div className="err-actions">
            <a className="btn" href="/">🏠 回首页</a>
            <a className="btn btn-teal" href="/works.html">🛠️ 看项目</a>
            <a className="btn btn-yellow" href="/contact.html">📬 来找我</a>
          </div>
        </div>
      </div>
    </section>
  );
}
