/**
 * 相册:瀑布流 + 分类筛选 + 灯箱。
 */
import { useMemo, useState } from 'react';
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { useApi } from '@/lib/useApi';
import type { Photo } from '@/lib/api';

export default function Gallery() {
  const { data, loading, error, reload } = useApi<Photo[]>('/api/content/photos');
  const [cat, setCat] = useState<string>('全部');
  const [active, setActive] = useState<number | null>(null);

  const photos = data ?? [];
  const cats = useMemo(() => {
    const set = new Set(photos.map((p) => p.category).filter(Boolean));
    return ['全部', ...Array.from(set)];
  }, [photos]);

  const shown = cat === '全部' ? photos : photos.filter((p) => p.category === cat);

  if (loading) return <Loading />;
  if (error) return <div className="mx-auto max-w-6xl px-5 py-10"><ErrorBox message={error} /><button className="btn mt-4" onClick={reload}>重试</button></div>;

  return (
    <PageShell title="相册" emoji="📷" subtitle="随手拍的一些瞬间">
      {/* 分类筛选 */}
      {cats.length > 1 && (
        <div className="mb-6 flex flex-wrap gap-2">
          {cats.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setCat(c)}
              className="pill"
              style={{
                background: cat === c ? 'var(--yellow)' : 'var(--paper)',
                color: cat === c ? '#2d2a32' : 'var(--ink)',
              }}
            >
              {c}
            </button>
          ))}
        </div>
      )}

      {shown.length === 0 && <Empty text="相册还是空的" />}

      {/* 瀑布流:按真实宽高预留占位,避免加载时跳动 */}
      <div className="columns-2 gap-4 sm:columns-3 lg:columns-4">
        {shown.map((p) => (
          <button
            key={p.id}
            type="button"
            onClick={() => setActive(p.id)}
            className="mb-4 block w-full break-inside-avoid overflow-hidden rounded-sticker border-[3px] text-left transition-transform hover:-translate-y-1"
            style={{ borderColor: 'var(--shadow)' }}
          >
            <img
              src={`/assets/uploads/${p.file}`}
              alt={p.title || '相册照片'}
              loading="lazy"
              className="w-full"
              style={{
                aspectRatio: p.width && p.height ? `${p.width} / ${p.height}` : undefined,
              }}
            />
            {(p.title || p.shot_at) && (
              <div className="px-3 py-2" style={{ background: 'var(--paper)' }}>
                {p.title && <p className="truncate text-sm font-bold">{p.title}</p>}
                {p.shot_at && (
                  <p className="text-xs" style={{ color: 'var(--text-3)' }}>
                    {p.shot_at}
                  </p>
                )}
              </div>
            )}
          </button>
        ))}
      </div>

      {/* 灯箱 */}
      {active !== null && (() => {
        const idx = shown.findIndex((p) => p.id === active);
        const cur = shown[idx];
        if (!cur) return null;
        const go = (d: number) => {
          const next = (idx + d + shown.length) % shown.length;
          setActive(shown[next].id);
        };
        return (
          <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/85 p-4"
            onClick={() => setActive(null)}
            role="dialog"
            aria-modal="true"
          >
            <button
              type="button"
              className="absolute right-5 top-4 text-3xl text-white"
              onClick={() => setActive(null)}
              aria-label="关闭"
            >
              ✕
            </button>
            <button
              type="button"
              className="absolute left-3 text-4xl text-white/80 hover:text-white"
              onClick={(e) => {
                e.stopPropagation();
                go(-1);
              }}
              aria-label="上一张"
            >
              ‹
            </button>
            <img
              src={`/assets/uploads/${cur.file}`}
              alt={cur.title || '相册照片'}
              className="max-h-[85vh] max-w-full rounded-xl object-contain"
              onClick={(e) => e.stopPropagation()}
            />
            <button
              type="button"
              className="absolute right-3 text-4xl text-white/80 hover:text-white"
              onClick={(e) => {
                e.stopPropagation();
                go(1);
              }}
              aria-label="下一张"
            >
              ›
            </button>
            {(cur.title || cur.desc) && (
              <div className="absolute bottom-6 max-w-lg px-4 text-center text-white">
                {cur.title && <p className="font-bold">{cur.title}</p>}
                {cur.desc && <p className="mt-1 text-sm opacity-80">{cur.desc}</p>}
              </div>
            )}
          </div>
        );
      })()}
    </PageShell>
  );
}
