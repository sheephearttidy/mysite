import React, { useEffect, useState } from 'react';
import Nav from './components/Nav.jsx';
import Footer from './components/Footer.jsx';
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
      <Nav pageId={pageId} />
      <main id="page-main">
        <Page onSeo={applySeo} />
      </main>
      <Footer />
    </>
  );
}
