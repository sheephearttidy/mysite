/**
 * 项目墙:封面配色卡片,支持外链。
 */
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { TiltedCard } from '@/components/TiltedCard';
import { SpotlightCard } from '@/components/SpotlightCard';
import { useApi } from '@/lib/useApi';
import type { PageData } from '@/lib/api';

const COVER: Record<string, { bg: string; fg: string }> = {
  pink: { bg: 'var(--pink-bg)', fg: 'var(--pink)' },
  yellow: { bg: 'var(--yellow-bg)', fg: '#8a6d00' },
  teal: { bg: 'var(--teal-bg)', fg: 'var(--teal)' },
  purple: { bg: 'var(--purple-bg)', fg: 'var(--purple)' },
  orange: { bg: 'var(--orange-bg)', fg: 'var(--orange)' },
  blue: { bg: 'var(--blue-bg)', fg: 'var(--blue)' },
};

export default function Works() {
  const { data, loading, error, reload } = useApi<PageData>('/api/page/works');

  if (loading) return <Loading />;
  if (error) return <div className="mx-auto max-w-6xl px-5 py-10"><ErrorBox message={error} /><button className="btn mt-4" onClick={reload}>重试</button></div>;
  if (!data) return null;

  const works = data.works ?? [];

  return (
    <PageShell title="我的小破项目们" emoji="🛠️" subtitle="从跑不起来的到勉强能用的">
      {works.length === 0 && <Empty text="项目还没配置" />}
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {works.map((w) => {
          const c = COVER[w.cover] ?? COVER.pink;
          const inner = (
            <SpotlightCard className="sticker sticker-hover h-full" color={`${c.fg}33`}>
              <div
                className="-mx-5 -mt-5 mb-4 flex h-24 items-center justify-center rounded-t-[15px] border-b-[3px] text-4xl"
                style={{ background: c.bg, borderColor: 'var(--shadow)' }}
              >
                {w.emoji}
              </div>
              <div className="flex items-start justify-between gap-2">
                <h3 className="font-round text-lg font-black">{w.title}</h3>
                {w.pill && (
                  <span className="pill shrink-0" style={{ background: c.bg, color: c.fg }}>
                    {w.pill}
                  </span>
                )}
              </div>
              <p className="mt-2 text-sm" style={{ color: 'var(--text-2)' }}>
                {w.desc}
              </p>
              {w.link && (
                <span className="mt-3 inline-block text-sm font-bold underline decoration-dotted" style={{ color: c.fg }}>
                  查看项目 →
                </span>
              )}
            </SpotlightCard>
          );

          return (
            <TiltedCard key={w.id} max={5}>
              {w.link ? (
                <a href={w.link} target="_blank" rel="noopener noreferrer" className="block h-full">
                  {inner}
                </a>
              ) : (
                inner
              )}
            </TiltedCard>
          );
        })}
      </div>
    </PageShell>
  );
}
