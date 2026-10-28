/**
 * 数据看板:今日/区间/累计、趋势、来源、城市、时段、最近明细。
 */
import { useApi } from '@/lib/useApi';
import { CountUp } from '@/components/CountUp';

interface Visits {
  today: number;
  range: number;
  total: number;
  bots: number;
  daily: { day: string; n: number }[];
  sources: { name: string; n: number }[];
  agents: { name: string; n: number }[];
  hours: number[];
  cities: { name: string; n: number }[];
  recent: { ts: number; path: string; ua: string; referer: string; city: string; dur_s: number }[];
}

export function Dashboard() {
  const { data, loading, error, reload } = useApi<Visits>('/api/stats/visits?days=14');

  if (loading) return <p style={{ color: 'var(--text-3)' }}>加载看板…</p>;
  if (error) {
    return (
      <div>
        <p className="text-sm font-bold" style={{ color: '#d64545' }}>⚠️ {error}</p>
        <button type="button" className="btn mt-3 text-sm" onClick={reload}>重试</button>
      </div>
    );
  }
  if (!data) return null;

  const maxDaily = Math.max(1, ...data.daily.map((d) => d.n));
  const maxHour = Math.max(1, ...data.hours);

  const cards = [
    { label: '今日访问', n: data.today, color: 'var(--pink)' },
    { label: '近 14 天', n: data.range, color: 'var(--teal)' },
    { label: '累计访问', n: data.total, color: 'var(--purple)' },
    { label: '已过滤爬虫', n: data.bots, color: 'var(--text-3)' },
  ];

  return (
    <div className="space-y-6">
      <h2 className="font-round text-xl font-black">📊 数据看板</h2>

      {/* 概览卡 */}
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {cards.map((c) => (
          <div key={c.label} className="sticker text-center">
            <p className="text-xs" style={{ color: 'var(--text-3)' }}>{c.label}</p>
            <p className="mt-1 font-round text-2xl font-black" style={{ color: c.color }}>
              <CountUp to={c.n} duration={1000} />
            </p>
          </div>
        ))}
      </div>

      {/* 趋势 */}
      <div className="sticker">
        <h3 className="mb-3 font-bold">📈 每日趋势</h3>
        <div className="flex h-32 items-end gap-1">
          {data.daily.map((d) => (
            <div key={d.day} className="group relative flex-1" title={`${d.day}: ${d.n}`}>
              <div
                className="w-full rounded-t transition-colors"
                style={{
                  height: `${Math.max(2, (d.n / maxDaily) * 100)}%`,
                  background: 'var(--pink)',
                }}
              />
            </div>
          ))}
        </div>
        <div className="mt-1 flex justify-between text-[10px]" style={{ color: 'var(--text-3)' }}>
          <span>{data.daily[0]?.day}</span>
          <span>{data.daily[data.daily.length - 1]?.day}</span>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {/* 来源 */}
        <div className="sticker">
          <h3 className="mb-2 font-bold">🔗 来源</h3>
          {data.sources.length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--text-3)' }}>暂无数据</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {data.sources.map((s) => (
                <li key={s.name} className="flex justify-between">
                  <span className="truncate">{s.name}</span>
                  <span className="font-bold">{s.n}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 城市 */}
        <div className="sticker">
          <h3 className="mb-2 font-bold">🏙️ 城市</h3>
          {data.cities.length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--text-3)' }}>暂无数据</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {data.cities.map((c) => (
                <li key={c.name} className="flex justify-between">
                  <span className="truncate">{c.name}</span>
                  <span className="font-bold">{c.n}</span>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* 时段 */}
        <div className="sticker">
          <h3 className="mb-2 font-bold">🕐 24 小时活跃</h3>
          <div className="flex h-20 items-end gap-0.5">
            {data.hours.map((n, h) => (
              <div
                key={h}
                className="flex-1 rounded-t"
                title={`${h}:00 — ${n}`}
                style={{
                  height: `${Math.max(2, (n / maxHour) * 100)}%`,
                  background: 'var(--teal)',
                }}
              />
            ))}
          </div>
        </div>

        {/* 浏览器 */}
        <div className="sticker">
          <h3 className="mb-2 font-bold">💻 浏览器 / 系统</h3>
          {data.agents.length === 0 ? (
            <p className="text-sm" style={{ color: 'var(--text-3)' }}>暂无数据</p>
          ) : (
            <ul className="space-y-1 text-sm">
              {data.agents.map((a) => (
                <li key={a.name} className="flex justify-between">
                  <span className="truncate">{a.name}</span>
                  <span className="font-bold">{a.n}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* 最近明细 */}
      <div className="sticker">
        <h3 className="mb-2 font-bold">🧾 最近访问</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead style={{ color: 'var(--text-3)' }}>
              <tr>
                <th className="py-1 text-left">时间</th>
                <th className="py-1 text-left">路径</th>
                <th className="py-1 text-left">来源</th>
                <th className="py-1 text-left">城市</th>
                <th className="py-1 text-left">停留</th>
              </tr>
            </thead>
            <tbody>
              {data.recent.map((r, i) => (
                <tr key={i} className="border-t" style={{ borderColor: 'var(--rule)' }}>
                  <td className="py-1">{new Date(r.ts * 1000).toLocaleString('zh-CN')}</td>
                  <td className="py-1">{r.path}</td>
                  <td className="py-1">{r.referer || '直接访问'}</td>
                  <td className="py-1">{r.city || '—'}</td>
                  <td className="py-1">{r.dur_s}s</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
