/**
 * 应用外壳:路由 + 公共布局(导航/页脚) + 访问上报。
 */
import { lazy, Suspense, useEffect } from 'react';
import { BrowserRouter, Route, Routes, useLocation } from 'react-router-dom';
import { Nav } from '@/components/Nav';
import { Footer } from '@/components/Footer';
import { Loading } from '@/components/PageShell';
import { useApi } from '@/lib/useApi';
import type { SiteInfo } from '@/lib/api';

const Home = lazy(() => import('@/pages/Home'));
const About = lazy(() => import('@/pages/About'));
const Skills = lazy(() => import('@/pages/Skills'));
const Works = lazy(() => import('@/pages/Works'));
const Campus = lazy(() => import('@/pages/Campus'));
const Gallery = lazy(() => import('@/pages/Gallery'));
const MapPage = lazy(() => import('@/pages/MapPage'));
const Contact = lazy(() => import('@/pages/Contact'));
const NotFound = lazy(() => import('@/pages/NotFound'));

/** 每个路径对应的服务端统计路径(只上报已知页面) */
const TRACK_MAP: Record<string, string> = {
  '/': '/',
  '/about': '/about.html',
  '/skills': '/skills.html',
  '/works': '/works.html',
  '/campus': '/campus.html',
  '/gallery': '/gallery.html',
  '/map': '/map.html',
  '/contact': '/contact.html',
};

function TrackVisit() {
  const { pathname } = useLocation();

  useEffect(() => {
    const serverPath = TRACK_MAP[pathname];
    if (!serverPath) return;
    // 同一标签页会话只报一次,刷新不刷量
    const key = 'tracked_paths';
    let tracked: string[] = [];
    try {
      tracked = JSON.parse(sessionStorage.getItem(key) ?? '[]');
    } catch {
      tracked = [];
    }
    if (tracked.includes(serverPath)) return;
    tracked.push(serverPath);
    try {
      sessionStorage.setItem(key, JSON.stringify(tracked));
    } catch {
      /* 忽略 */
    }
    // sendBeacon 不阻塞页面
    const payload = JSON.stringify({ path: serverPath, referer: document.referrer });
    if (navigator.sendBeacon) {
      navigator.sendBeacon('/api/track', new Blob([payload], { type: 'application/json' }));
    } else {
      void fetch('/api/track', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: payload,
        keepalive: true,
      }).catch(() => undefined);
    }
  }, [pathname]);

  return null;
}

function Shell({ site }: { site: SiteInfo | null }) {
  return (
    <div className="flex min-h-screen flex-col">
      <Nav siteName={site?.site_name ?? '我的小窝'} />
      <div className="flex-1">
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/about" element={<About />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/works" element={<Works />} />
            <Route path="/campus" element={<Campus />} />
            <Route path="/gallery" element={<Gallery />} />
            <Route path="/map" element={<MapPage />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
      </div>
      <Footer
        owner={site?.site_owner ?? '至尊杰'}
        credit={site?.site_credit ?? '纯手搓 + AI 协作'}
        startYear={site?.site_start_year ?? '2026'}
      />
    </div>
  );
}

export default function App() {
  // 站点信息用于导航与页脚,失败也不阻塞页面
  const { data: site } = useApi<SiteInfo>('/api/site');

  return (
    <BrowserRouter>
      <TrackVisit />
      <Shell site={site} />
    </BrowserRouter>
  );
}
