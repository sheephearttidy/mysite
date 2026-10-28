/**
 * 关于我:自我介绍段落 + 信息卡片 + 荣誉墙 + 最近在听。
 */
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { TiltedCard } from '@/components/TiltedCard';
import { SpotlightCard } from '@/components/SpotlightCard';
import { useApi } from '@/lib/useApi';
import type { PageData } from '@/lib/api';

const LEVEL_LABEL: Record<string, string> = {
  national: '国家级',
  provincial: '省级',
  school: '校级',
  other: '其他',
};

export default function About() {
  const { data, loading, error, reload } = useApi<PageData>('/api/page/about');

  if (loading) return <Loading />;
  if (error) return <div className="mx-auto max-w-6xl px-5 py-10"><ErrorBox message={error} /><button className="btn mt-4" onClick={reload}>重试</button></div>;
  if (!data) return null;

  const { profile = [], honors = [], songs = [] } = data;
  const about = profile.filter((p) => p.kind === 'about');
  const info = profile.filter((p) => p.kind === 'info');

  return (
    <PageShell title="关于我这只人类" emoji="🧍" subtitle="一些不太正经但真实的自我介绍">
      <div className="grid gap-6 lg:grid-cols-3">
        {/* 左:自我介绍段落 */}
        <div className="space-y-4 lg:col-span-2">
          {about.length === 0 && <Empty text="还没有自我介绍" />}
          {about.map((p) => (
            <SpotlightCard key={p.id} className="sticker sticker-hover">
              <h3 className="font-round text-lg font-black" style={{ color: 'var(--pink)' }}>
                {p.label}
              </h3>
              <p className="mt-2" style={{ color: 'var(--text-2)' }}>
                {p.value}
              </p>
            </SpotlightCard>
          ))}
        </div>

        {/* 右:信息卡片 */}
        <aside className="space-y-3">
          {info.map((p) => (
            <TiltedCard key={p.id}>
              <div
                className="flex items-center gap-3 rounded-sticker border-[3px] px-4 py-3"
                style={{ borderColor: 'var(--shadow)', background: 'var(--paper)' }}
              >
                <span className="text-2xl">{p.emoji}</span>
                <div>
                  <p className="text-xs font-bold" style={{ color: 'var(--text-3)' }}>
                    {p.label}
                  </p>
                  <p className="font-bold">{p.value}</p>
                </div>
              </div>
            </TiltedCard>
          ))}
        </aside>
      </div>

      {/* 荣誉墙 */}
      {honors.length > 0 && (
        <section className="mt-12">
          <h2 className="mb-5 font-round text-2xl font-black">🏆 荣誉墙</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {honors.map((h) => (
              <div key={h.id} className="sticker sticker-hover">
                <div className="flex items-start gap-3">
                  <span className="text-2xl">{h.emoji}</span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="pill" style={{ background: 'var(--yellow-bg)', color: '#8a6d00' }}>
                        {h.year}
                      </span>
                      <span className="pill" style={{ background: 'var(--teal-bg)', color: 'var(--teal)' }}>
                        {LEVEL_LABEL[h.level] ?? h.level}
                      </span>
                    </div>
                    <h3 className="mt-2 font-bold">{h.title}</h3>
                    {h.desc && (
                      <p className="mt-1 text-sm" style={{ color: 'var(--text-2)' }}>
                        {h.desc}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 最近在听 */}
      {songs.length > 0 && (
        <section className="mt-12">
          <h2 className="mb-5 font-round text-2xl font-black">🎧 最近在听</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {songs.map((s) => (
              <div key={s.id} className="sticker">
                <div className="flex items-center gap-3">
                  <span className="text-2xl">{s.emoji}</span>
                  <div className="min-w-0">
                    <p className="truncate font-bold">{s.title}</p>
                    <p className="text-xs" style={{ color: 'var(--text-3)' }}>
                      {s.artist}
                    </p>
                  </div>
                </div>
                {s.note && (
                  <p className="mt-2 text-sm" style={{ color: 'var(--text-2)' }}>
                    {s.note}
                  </p>
                )}
                <iframe
                  title={`播放 ${s.title}`}
                  className="mt-3 w-full rounded-xl"
                  height="86"
                  frameBorder="0"
                  loading="lazy"
                  src={`https://i.y.qq.com/n2/m/outchain/player/index.html?songid=${s.song_id}`}
                />
              </div>
            ))}
          </div>
        </section>
      )}
    </PageShell>
  );
}
