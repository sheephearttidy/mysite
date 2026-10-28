/**
 * 校园日常:时间线 + 随手记瀑布流。
 */
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { useApi } from '@/lib/useApi';
import type { PageData } from '@/lib/api';

const MOOD: Record<string, string> = {
  pink: 'var(--pink-bg)',
  yellow: 'var(--yellow-bg)',
  teal: 'var(--teal-bg)',
  purple: 'var(--purple-bg)',
  orange: 'var(--orange-bg)',
  blue: 'var(--blue-bg)',
};

export default function Campus() {
  const { data, loading, error, reload } = useApi<PageData>('/api/page/campus');

  if (loading) return <Loading />;
  if (error) return <div className="mx-auto max-w-6xl px-5 py-10"><ErrorBox message={error} /><button className="btn mt-4" onClick={reload}>重试</button></div>;
  if (!data) return null;

  const timeline = data.timeline ?? [];
  const notes = data.notes ?? [];

  return (
    <PageShell title="校园打怪升级记录" emoji="🗺️" subtitle="从开学到现在的一路折腾">
      {/* 时间线 */}
      <section>
        <h2 className="mb-5 font-round text-xl font-black">📖 时间线</h2>
        {timeline.length === 0 ? (
          <Empty text="时间线还没配置" />
        ) : (
          <ol className="relative space-y-6 border-l-[3px] pl-6" style={{ borderColor: 'var(--rule)' }}>
            {timeline.map((t) => (
              <li key={t.id} className="relative">
                <span
                  className="absolute -left-[2.15rem] flex h-8 w-8 items-center justify-center rounded-full border-[3px] text-sm"
                  style={{ borderColor: 'var(--shadow)', background: 'var(--yellow)' }}
                >
                  {t.emoji}
                </span>
                <div className="sticker sticker-hover">
                  <p className="text-xs font-black tracking-wider" style={{ color: 'var(--pink)' }}>
                    {t.time_label}
                  </p>
                  <h3 className="mt-1 font-round text-lg font-black">{t.title}</h3>
                  {t.content && (
                    <p className="mt-2 text-sm" style={{ color: 'var(--text-2)' }}>
                      {t.content}
                    </p>
                  )}
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>

      {/* 随手记 */}
      <section className="mt-12">
        <h2 className="mb-5 font-round text-xl font-black">📝 随手记</h2>
        {notes.length === 0 ? (
          <Empty text="还没有随手记" />
        ) : (
          <div className="columns-1 gap-4 sm:columns-2 lg:columns-3">
            {notes.map((n, i) => (
              <div
                key={n.id}
                className="mb-4 break-inside-avoid rounded-sticker border-[3px] p-4"
                style={{
                  borderColor: 'var(--shadow)',
                  background: MOOD[n.mood] ?? 'var(--paper)',
                  transform: `rotate(${(i % 3) - 1}deg)`,
                }}
              >
                <span className="text-xl">{n.emoji}</span>
                <p className="mt-1 font-bold leading-relaxed">{n.text}</p>
              </div>
            ))}
          </div>
        )}
      </section>
    </PageShell>
  );
}
