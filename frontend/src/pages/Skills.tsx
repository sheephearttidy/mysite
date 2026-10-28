/**
 * 技能树:认真技能 / 被动技能 两栏,进度条带入场动画。
 */
import { useEffect, useRef, useState } from 'react';
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { useApi } from '@/lib/useApi';
import type { PageData, Skill } from '@/lib/api';

const COLOR_VAR: Record<string, string> = {
  pink: 'var(--pink)',
  yellow: 'var(--yellow)',
  teal: 'var(--teal)',
  purple: 'var(--purple)',
  orange: 'var(--orange)',
  blue: 'var(--blue)',
};

function SkillBar({ skill }: { skill: Skill }) {
  const ref = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(0);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      setW(skill.percent);
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          // 下一帧再设宽度,保证 transition 生效
          requestAnimationFrame(() => setW(skill.percent));
          io.disconnect();
        }
      },
      { threshold: 0.3 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [skill.percent]);

  return (
    <div className="sticker sticker-hover" ref={ref}>
      <div className="flex items-baseline justify-between gap-2">
        <span className="font-bold">{skill.name}</span>
        <span className="font-round text-lg font-black" style={{ color: COLOR_VAR[skill.color] }}>
          {skill.percent}%
        </span>
      </div>
      <div
        className="mt-2 h-3 overflow-hidden rounded-full border-2"
        style={{ borderColor: 'var(--shadow)', background: 'var(--cream)' }}
      >
        <div
          className="h-full rounded-full transition-[width] duration-1000 ease-out"
          style={{ width: `${w}%`, background: COLOR_VAR[skill.color] }}
        />
      </div>
      {skill.note && (
        <p className="mt-2 text-xs" style={{ color: 'var(--text-3)' }}>
          {skill.note}
        </p>
      )}
    </div>
  );
}

export default function Skills() {
  const { data, loading, error, reload } = useApi<PageData>('/api/page/skills');

  if (loading) return <Loading />;
  if (error) return <div className="mx-auto max-w-6xl px-5 py-10"><ErrorBox message={error} /><button className="btn mt-4" onClick={reload}>重试</button></div>;
  if (!data) return null;

  const skills = data.skills ?? [];
  const serious = skills.filter((s) => s.category === 'serious');
  const passive = skills.filter((s) => s.category === 'passive');

  return (
    <PageShell title="技能树" emoji="🎯" subtitle="认真练的,和认真摆烂的">
      {skills.length === 0 && <Empty text="技能还没配置" />}
      <div className="grid gap-8 lg:grid-cols-2">
        <section>
          <h2 className="mb-4 font-round text-xl font-black">💪 认真技能</h2>
          <div className="space-y-4">
            {serious.map((s) => (
              <SkillBar key={s.id} skill={s} />
            ))}
            {serious.length === 0 && <Empty text="还没有认真技能" />}
          </div>
        </section>
        <section>
          <h2 className="mb-4 font-round text-xl font-black">🛌 被动技能</h2>
          <div className="space-y-4">
            {passive.map((s) => (
              <SkillBar key={s.id} skill={s} />
            ))}
            {passive.length === 0 && <Empty text="还没有被动技能" />}
          </div>
        </section>
      </div>
    </PageShell>
  );
}
