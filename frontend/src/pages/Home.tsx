/**
 * 首页:首屏(粒子背景 + 渐变标题 + 打字机) + 数据统计 + 那年今日。
 */
import { Link } from 'react-router-dom';
import { Aurora } from '@/components/Aurora';
import { Particles } from '@/components/Particles';
import { GridBackground } from '@/components/GridBackground';
import { Meteors } from '@/components/Meteors';
import { CountUp } from '@/components/CountUp';
import { SplitText } from '@/components/SplitText';
import { GradientText } from '@/components/GradientText';
import { TextType } from '@/components/TextType';
import { ShinyText } from '@/components/ShinyText';
import { SpotlightCard } from '@/components/SpotlightCard';
import { Empty, ErrorBox, Loading } from '@/components/PageShell';
import { useApi } from '@/lib/useApi';
import type { PageData } from '@/lib/api';

const COLOR_MAP: Record<string, { bg: string; fg: string }> = {
  pink: { bg: 'var(--pink-bg)', fg: 'var(--pink)' },
  yellow: { bg: 'var(--yellow-bg)', fg: '#8a6d00' },
  teal: { bg: 'var(--teal-bg)', fg: 'var(--teal)' },
  purple: { bg: 'var(--purple-bg)', fg: 'var(--purple)' },
  orange: { bg: 'var(--orange-bg)', fg: 'var(--orange)' },
  blue: { bg: 'var(--blue-bg)', fg: 'var(--blue)' },
};

export default function Home() {
  const { data, loading, error, reload } = useApi<PageData>('/api/page/index');

  if (loading) return <Loading />;
  if (error) {
    return (
      <div className="mx-auto max-w-6xl px-5 py-10">
        <ErrorBox message={error} />
        <button type="button" className="btn mt-4" onClick={reload}>重试</button>
      </div>
    );
  }
  if (!data) return null;

  const { site, stats = [], onthisday = [] } = data;

  return (
    <>
      {/* ---------- 首屏 ---------- */}
      <section className="relative overflow-hidden">
        <Aurora opacity={0.42} />
        <Particles count={70} />
        <GridBackground size={52} spotSize={300} />
        <Meteors number={12} />

        <div className="relative mx-auto max-w-6xl px-5 py-20 sm:py-28">
          <p
            className="mb-4 inline-block rounded-full border-[3px] px-4 py-1 text-xs font-black tracking-wider"
            style={{ borderColor: 'var(--shadow)', background: 'var(--yellow)', color: '#2d2a32' }}
          >
            🏫 {site.site_school} · {site.site_major}
          </p>

          <h1 className="font-round text-4xl font-black leading-tight sm:text-6xl">
            <SplitText text="你好,我是" delay={45} />{' '}
            <GradientText duration={7} className="font-round">
              {site.site_owner}
            </GradientText>
          </h1>

          <p className="mt-5 max-w-2xl text-lg" style={{ color: 'var(--text-2)' }}>
            <TextType
              text={[
                `${site.site_grade} · 沉迷${site.site_focus}`,
                site.site_slogan,
                '写代码、调小车、折腾 AI',
              ]}
              speed={80}
            />
          </p>

          <p className="mt-2 text-sm" style={{ color: 'var(--text-3)' }}>
            <ShinyText duration={5}>{site.site_credit}</ShinyText>
          </p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/works" className="btn btn-accent">🛠️ 看看我的项目</Link>
            <Link to="/about" className="btn">🧍 关于我</Link>
            <Link to="/contact" className="btn">✉️ 来找我玩</Link>
          </div>
        </div>
      </section>

      {/* ---------- 不正经数据统计 ---------- */}
      {stats.length > 0 && (
        <section className="mx-auto max-w-6xl px-5 py-10">
          <h2 className="mb-6 font-round text-2xl font-black">🧮 不正经数据统计</h2>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {stats.map((s) => (
              <SpotlightCard key={s.id} className="sticker sticker-hover">
                <div className="text-center">
                  <div className="text-3xl">{s.emoji}</div>
                  <div className="mt-2 font-round text-3xl font-black" style={{ color: 'var(--pink)' }}>
                    <CountUp to={s.number} separator />
                    <span className="ml-0.5 text-base">{s.unit}</span>
                  </div>
                  <p className="mt-1 text-xs" style={{ color: 'var(--text-2)' }}>{s.label}</p>
                </div>
              </SpotlightCard>
            ))}
          </div>
        </section>
      )}

      {/* ---------- 那年今日 ---------- */}
      {onthisday.length > 0 && (
        <section className="mx-auto max-w-6xl px-5 py-10">
          <h2 className="mb-6 font-round text-2xl font-black">📅 那年今日</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {onthisday.map((item, i) => {
              const c = COLOR_MAP[item.mood ?? 'teal'] ?? COLOR_MAP.teal;
              return (
                <div key={i} className="sticker" style={{ background: c.bg }}>
                  <p className="text-xs font-bold" style={{ color: 'var(--text-2)' }}>
                    {item.years_ago} 年前的今天
                  </p>
                  {item.kind === 'note' ? (
                    <p className="mt-2">{item.emoji} {item.text}</p>
                  ) : (
                    <div className="mt-2">
                      <img
                        src={`/assets/uploads/${item.file}`}
                        alt={item.title || '往年照片'}
                        loading="lazy"
                        className="w-full rounded-xl border-2 object-cover"
                        style={{ borderColor: 'var(--shadow)' }}
                      />
                      {item.title && <p className="mt-2 text-sm">{item.title}</p>}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {stats.length === 0 && onthisday.length === 0 && (
        <div className="mx-auto max-w-6xl px-5 py-10">
          <Empty text="首页内容还没配置,去后台加几条吧" />
        </div>
      )}
    </>
  );
}
