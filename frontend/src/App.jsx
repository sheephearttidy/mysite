import React, { useEffect, useState } from 'react';
import Nav from './components/Nav.jsx';
import Footer from './components/Footer.jsx';
import Lightfall from './components/Lightfall.jsx';
import { currentPageId } from './lib/router.js';
import { applySeo } from './lib/seo.js';

import HomePage from './pages/Home.jsx';
import AboutPage from './pages/About.jsx';
import SkillsPage from './pages/Skills.jsx';
import WorksPage from './pages/Works.jsx';
import CampusPage from './pages/Campus.jsx';
import GalleryPage from './pages/Gallery.jsx';
import MapPage from './pages/Map.jsx';
import ContactPage from './pages/Contact.jsx';
import NotFoundPage from './pages/NotFound.jsx';

const PAGE_COMPONENTS = {
  index: HomePage,
  about: AboutPage,
  skills: SkillsPage,
  works: WorksPage,
  campus: CampusPage,
  gallery: GalleryPage,
  map: MapPage,
  contact: ContactPage,
};

/**
 * 全站背景:Lightfall 光带效果。
 *
 * 性能与体验考量:
 * - 固定在视口底层(position: fixed; z-index: 0),内容层叠在它上面
 * - 尊重系统「减少动态效果」设置:开了就暂停动画,只留一帧静态光
 * - 小屏/低端设备降参(减少光带层数与 bloom),避免掉帧
 * - 页面隐藏时组件内部会自动停帧,不空耗 GPU
 */
function Backdrop() {
  const [calm, setCalm] = useState(false);
  const [compact, setCompact] = useState(false);

  useEffect(() => {
    const mqReduce = window.matchMedia('(prefers-reduced-motion: reduce)');
    const mqNarrow = window.matchMedia('(max-width: 720px)');
    const sync = () => {
      setCalm(mqReduce.matches);
      setCompact(mqNarrow.matches);
    };
    sync();
    mqReduce.addEventListener?.('change', sync);
    mqNarrow.addEventListener?.('change', sync);
    return () => {
      mqReduce.removeEventListener?.('change', sync);
      mqNarrow.removeEventListener?.('change', sync);
    };
  }, []);

  return (
    <div className="site-backdrop" aria-hidden="true">
      <Lightfall
        colors={['#ffd93d', '#ff6b9d', '#7ec8b8', '#ffffff']}
        backgroundColor="#1b1922"
        speed={calm ? 0.12 : 0.3}
        streakCount={compact ? 6 : 12}
        streakWidth={0.8}
        streakLength={1.1}
        density={0.6}
        twinkle={0.3}
        glow={0.9}
        backgroundGlow={0.14}
        headGlow={0.6}
        depth={0.55}
        bloom={compact ? 0.25 : 0.4}
        zoom={3}
        opacity={0.55}
        mouseInteraction={!calm && !compact}
        mouseStrength={0.35}
        mouseRadius={0.45}
        lens={0.45}
        holdToWarp={!calm}
        intro
        fade={0.35}
        paused={calm}
      />
    </div>
  );
}

export default function App({ initialPage }) {
  const [pageId, setPageId] = useState(initialPage || currentPageId());

  useEffect(() => {
    const onPop = () => setPageId(currentPageId());
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  // 页面切换时滚动到顶部(和传统多页站行为一致)
  useEffect(() => {
    window.scrollTo(0, 0);
  }, [pageId]);

  const Page = PAGE_COMPONENTS[pageId] || NotFoundPage;

  return (
    <>
      <Backdrop />
      <div className="site-content">
        <Nav pageId={pageId} />
        <main id="page-main">
          <Page onSeo={applySeo} />
        </main>
        <Footer />
      </div>
    </>
  );
}
