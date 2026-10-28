/**
 * 来访地图:城市排行 + 简化世界地图钉点。
 * 城市坐标表从原站 js/cities.js 迁移而来(取常用城市)。
 */
import { useMemo } from 'react';
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { CountUp } from '@/components/CountUp';
import { useApi } from '@/lib/useApi';

interface CityPoint {
  city: string;
  n: number;
}

// 经纬度 -> 等距圆柱投影的百分比坐标
const CITY_COORDS: Record<string, [number, number]> = {
  北京: [116.4, 39.9], 上海: [121.5, 31.2], 广州: [113.3, 23.1], 深圳: [114.1, 22.5],
  杭州: [120.2, 30.3], 南京: [118.8, 32.1], 成都: [104.1, 30.7], 武汉: [114.3, 30.6],
  西安: [108.9, 34.3], 重庆: [106.5, 29.6], 天津: [117.2, 39.1], 苏州: [120.6, 31.3],
  长沙: [113.0, 28.2], 郑州: [113.6, 34.7], 青岛: [120.4, 36.1], 沈阳: [123.4, 41.8],
  大连: [121.6, 38.9], 厦门: [118.1, 24.5], 福州: [119.3, 26.1], 合肥: [117.3, 31.9],
  昆明: [102.7, 25.0], 哈尔滨: [126.6, 45.8], 济南: [117.0, 36.7], 石家庄: [114.5, 38.0],
  太原: [112.5, 37.9], 南昌: [115.9, 28.7], 贵阳: [106.6, 26.6], 南宁: [108.4, 22.8],
  兰州: [103.8, 36.1], 乌鲁木齐: [87.6, 43.8], 香港: [114.2, 22.3], 澳门: [113.5, 22.2],
  台北: [121.5, 25.0], 拉萨: [91.1, 29.6], 银川: [106.3, 38.5], 西宁: [101.8, 36.6],
};

function project(lng: number, lat: number): { x: number; y: number } {
  // 简化的中国区域视图,把经纬度映射到 0~100%
  const x = ((lng - 73) / (135 - 73)) * 100;
  const y = ((54 - lat) / (54 - 18)) * 100;
  return { x: Math.max(2, Math.min(98, x)), y: Math.max(2, Math.min(98, y)) };
}

export default function MapPage() {
  const { data, loading, error, reload } = useApi<CityPoint[]>('/api/map');
  const points = data ?? [];

  const max = useMemo(() => Math.max(1, ...points.map((p) => p.n)), [points]);

  if (loading) return <Loading />;
  if (error) return <div className="mx-auto max-w-6xl px-5 py-10"><ErrorBox message={error} /><button className="btn mt-4" onClick={reload}>重试</button></div>;

  return (
    <PageShell title="来访地图" emoji="🌍" subtitle="只记录城市,不记录 IP">
      <div className="grid gap-6 lg:grid-cols-3">
        {/* 地图 */}
        <div className="lg:col-span-2">
          <div
            className="sticker relative aspect-[16/10] overflow-hidden"
            style={{ background: 'var(--blue-bg)' }}
          >
            {points.length === 0 ? (
              <div className="flex h-full items-center justify-center text-sm" style={{ color: 'var(--text-3)' }}>
                还没有访客数据
              </div>
            ) : (
              <>
                {points.map((p) => {
                  const base = p.city.split(' ').pop() ?? p.city;
                  const coord = CITY_COORDS[base];
                  if (!coord) return null;
                  const { x, y } = project(coord[0], coord[1]);
                  const size = 8 + (p.n / max) * 18;
                  return (
                    <span
                      key={p.city}
                      className="absolute -translate-x-1/2 -translate-y-1/2 rounded-full border-2"
                      title={`${p.city} · ${p.n} 次`}
                      style={{
                        left: `${x}%`,
                        top: `${y}%`,
                        width: size,
                        height: size,
                        background: 'var(--yellow)',
                        borderColor: 'var(--shadow)',
                        boxShadow: '2px 2px 0 var(--shadow)',
                      }}
                    />
                  );
                })}
                <p
                  className="absolute bottom-2 right-3 text-xs"
                  style={{ color: 'var(--text-3)' }}
                >
                  点越大 = 访问越多
                </p>
              </>
            )}
          </div>
        </div>

        {/* 排行 */}
        <aside>
          <h2 className="mb-4 font-round text-xl font-black">🏙️ 城市排行</h2>
          {points.length === 0 ? (
            <Empty text="暂无数据" />
          ) : (
            <ol className="space-y-2">
              {points.slice(0, 15).map((p, i) => (
                <li
                  key={p.city}
                  className="flex items-center gap-3 rounded-xl border-2 px-3 py-2"
                  style={{ borderColor: 'var(--rule)', background: 'var(--paper)' }}
                >
                  <span className="w-6 text-center text-xs font-black" style={{ color: 'var(--text-3)' }}>
                    {i + 1}
                  </span>
                  <span className="flex-1 truncate text-sm font-bold">{p.city}</span>
                  <span className="font-round font-black" style={{ color: 'var(--pink)' }}>
                    <CountUp to={p.n} duration={900} />
                  </span>
                </li>
              ))}
            </ol>
          )}
        </aside>
      </div>
    </PageShell>
  );
}
