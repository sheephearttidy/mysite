/**
 * 来访地图:真实世界地图 + 城市点位。
 *
 * 底图用预投影的世界国界数据(lib/worldMap.ts,由 gen_world_map.py 生成),
 * 城市点位用同一个 project() 投影,保证经纬度与底图严格对齐。
 */
import { useMemo, useState } from 'react';
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { CountUp } from '@/components/CountUp';
import { MAP_VIEW, WORLD_PATHS, project } from '@/lib/worldMap';
import { useApi } from '@/lib/useApi';

interface CityPoint {
  city: string;
  n: number;
}

/** 城市名 -> 经纬度。键为城市名本身(去掉省份前缀后匹配)。 */
const CITY_COORDS: Record<string, [number, number]> = {
  // 中国主要城市
  北京: [116.41, 39.90], 上海: [121.47, 31.23], 广州: [113.26, 23.13],
  深圳: [114.06, 22.55], 杭州: [120.15, 30.28], 南京: [118.80, 32.06],
  成都: [104.07, 30.67], 武汉: [114.30, 30.59], 西安: [108.94, 34.34],
  重庆: [106.55, 29.56], 天津: [117.20, 39.13], 苏州: [120.59, 31.30],
  长沙: [112.94, 28.23], 郑州: [113.63, 34.75], 青岛: [120.38, 36.07],
  沈阳: [123.43, 41.81], 大连: [121.61, 38.91], 厦门: [118.09, 24.48],
  福州: [119.30, 26.08], 合肥: [117.28, 31.86], 昆明: [102.71, 25.04],
  哈尔滨: [126.53, 45.80], 济南: [117.00, 36.67], 石家庄: [114.51, 38.04],
  太原: [112.55, 37.87], 南昌: [115.89, 28.68], 贵阳: [106.63, 26.65],
  南宁: [108.37, 22.82], 兰州: [103.83, 36.06], 乌鲁木齐: [87.62, 43.82],
  香港: [114.17, 22.32], 澳门: [113.55, 22.20], 台北: [121.52, 25.03],
  拉萨: [91.11, 29.65], 银川: [106.28, 38.47], 西宁: [101.78, 36.62],
  呼和浩特: [111.75, 40.84], 海口: [110.20, 20.04], 三亚: [109.51, 18.25],
  // 河北(站主所在地,数据最多)
  唐山: [118.18, 39.63], 廊坊: [116.68, 39.52], 承德: [117.94, 40.98],
  保定: [115.46, 38.87], 秦皇岛: [119.60, 39.94], 邯郸: [114.49, 36.61],
  邢台: [114.51, 37.07], 沧州: [116.84, 38.30], 张家口: [114.89, 40.82],
  衡水: [115.67, 37.74], 定州: [114.99, 38.52], 辛集: [115.22, 37.94],
  迁安: [118.70, 40.01], 遵化: [117.96, 40.19], 三河: [117.08, 39.98],
  // 港澳台与海外
  东京: [139.69, 35.69], 大阪: [135.50, 34.69], 首尔: [126.98, 37.57],
  新加坡: [103.82, 1.35], 曼谷: [100.50, 13.75], 吉隆坡: [101.69, 3.14],
  伦敦: [-0.13, 51.51], 巴黎: [2.35, 48.86], 柏林: [13.40, 52.52],
  阿姆斯特丹: [4.90, 52.37], 法兰克福: [8.68, 50.11], 都柏林: [-6.26, 53.35],
  纽约: [-74.01, 40.71], 洛杉矶: [-118.24, 34.05], 旧金山: [-122.42, 37.77],
  西雅图: [-122.33, 47.61], 芝加哥: [-87.63, 41.88], 达拉斯: [-96.80, 32.78],
  多伦多: [-79.38, 43.65], 温哥华: [-123.12, 49.28], 悉尼: [151.21, -33.87],
  墨尔本: [144.96, -37.81], 迪拜: [55.27, 25.20], 孟买: [72.88, 19.08],
  雅加达: [106.85, -6.21], 马尼拉: [120.98, 14.60], 河内: [105.83, 21.03],
  // ip-api 常见的英文城市名
  Ashburn: [-77.49, 39.04], 馬納薩斯: [-77.47, 38.75], 曼萨萨斯: [-77.47, 38.75],
  Manassas: [-77.47, 38.75], Boardman: [-119.70, 45.84], Seattle: [-122.33, 47.61],
  Singapore: [103.82, 1.35], Tokyo: [139.69, 35.69], Seoul: [126.98, 37.57],
  Frankfurt: [8.68, 50.11], London: [-0.13, 51.51], Paris: [2.35, 48.86],
  Amsterdam: [4.90, 52.37], Dublin: [-6.26, 53.35], Toronto: [-79.38, 43.65],
  Sydney: [151.21, -33.87], Melbourne: [144.96, -37.81],
};

/** 解析城市名:兼容「河北 石家庄」「美国 Ashburn」「日本」等格式 */
function resolveCoord(city: string): [number, number] | null {
  const parts = city.trim().split(/\s+/);
  // 从后往前找,优先匹配更具体的城市名
  for (let i = parts.length - 1; i >= 0; i -= 1) {
    const key = parts[i];
    if (CITY_COORDS[key]) return CITY_COORDS[key];
  }
  return null;
}

export default function MapPage() {
  const { data, loading, error, reload } = useApi<CityPoint[]>('/api/map');
  const [hover, setHover] = useState<string | null>(null);

  const points = data ?? [];
  const max = useMemo(() => Math.max(1, ...points.map((p) => p.n)), [points]);

  const { placed, unplaced } = useMemo(() => {
    const ok: { city: string; n: number; x: number; y: number }[] = [];
    const no: CityPoint[] = [];
    for (const p of points) {
      const coord = resolveCoord(p.city);
      if (!coord) {
        no.push(p);
        continue;
      }
      const { x, y } = project(coord[0], coord[1]);
      ok.push({ city: p.city, n: p.n, x, y });
    }
    return { placed: ok, unplaced: no };
  }, [points]);

  if (loading) return <Loading />;
  if (error) {
    return (
      <div className="mx-auto max-w-6xl px-5 py-10">
        <ErrorBox message={error} />
        <button type="button" className="btn mt-4" onClick={reload}>重试</button>
      </div>
    );
  }

  return (
    <PageShell title="来访地图" emoji="🌍" subtitle="只记录城市,不记录 IP">
      <div className="grid gap-6 lg:grid-cols-3">
        {/* 世界地图 */}
        <div className="lg:col-span-2">
          <div className="sticker overflow-hidden p-3">
            <svg
              viewBox={`0 0 ${MAP_VIEW.width} ${MAP_VIEW.height}`}
              className="w-full rounded-xl"
              style={{ background: 'var(--blue-bg)' }}
              role="img"
              aria-label="访客城市分布世界地图"
            >
              {/* 经纬网 */}
              <g stroke="var(--rule)" strokeWidth="0.5" opacity="0.45">
                {[-150, -120, -90, -60, -30, 0, 30, 60, 90, 120, 150].map((lng) => {
                  const { x } = project(lng, 0);
                  return <line key={`v${lng}`} x1={x} y1={0} x2={x} y2={MAP_VIEW.height} />;
                })}
                {[-60, -30, 0, 30, 60].map((lat) => {
                  const { y } = project(0, lat);
                  return <line key={`h${lat}`} x1={0} y1={y} x2={MAP_VIEW.width} y2={y} />;
                })}
              </g>

              {/* 国界轮廓 */}
              <g
                fill="var(--teal-bg)"
                stroke="var(--teal)"
                strokeWidth="0.6"
                strokeLinejoin="round"
                opacity="0.95"
              >
                {WORLD_PATHS.map((d, i) => (
                  <path key={i} d={d} />
                ))}
              </g>

              {/* 城市点位 */}
              {placed.map((p) => {
                const r = 3.5 + (p.n / max) * 11;
                const active = hover === p.city;
                return (
                  <g
                    key={p.city}
                    onMouseEnter={() => setHover(p.city)}
                    onMouseLeave={() => setHover(null)}
                    style={{ cursor: 'pointer' }}
                  >
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={r + 4}
                      fill="var(--pink)"
                      opacity={active ? 0.35 : 0.16}
                    />
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={r}
                      fill="var(--yellow)"
                      stroke="var(--shadow)"
                      strokeWidth="1.2"
                    />
                    {active && (
                      <g>
                        <rect
                          x={p.x + r + 5}
                          y={p.y - 19}
                          width={Math.max(76, p.city.length * 12 + 46)}
                          height="22"
                          rx="5"
                          fill="var(--paper)"
                          stroke="var(--shadow)"
                          strokeWidth="1.2"
                        />
                        <text
                          x={p.x + r + 10}
                          y={p.y - 4}
                          fontSize="12"
                          fontWeight="700"
                          fill="var(--ink)"
                        >
                          {p.city} · {p.n} 次
                        </text>
                      </g>
                    )}
                  </g>
                );
              })}
            </svg>

            <p className="mt-2 text-center text-xs" style={{ color: 'var(--text-3)' }}>
              圆点越大 = 访问越多
              {unplaced.length > 0 && ` · ${unplaced.length} 个城市未在坐标表中`}
            </p>
          </div>
        </div>

        {/* 排行 */}
        <aside>
          <h2 className="mb-4 font-round text-xl font-black">🏙️ 城市排行</h2>
          {points.length === 0 ? (
            <Empty text="暂无数据" />
          ) : (
            <ol className="space-y-2">
              {points.slice(0, 15).map((p, i) => {
                const known = resolveCoord(p.city) !== null;
                return (
                  <li
                    key={p.city}
                    className="flex items-center gap-3 rounded-xl border-2 px-3 py-2"
                    style={{
                      borderColor: hover === p.city ? 'var(--pink)' : 'var(--rule)',
                      background: 'var(--paper)',
                    }}
                    onMouseEnter={() => setHover(p.city)}
                    onMouseLeave={() => setHover(null)}
                  >
                    <span
                      className="w-6 text-center text-xs font-black"
                      style={{ color: 'var(--text-3)' }}
                    >
                      {i + 1}
                    </span>
                    <span className="flex-1 truncate text-sm font-bold">
                      {known ? p.city : `${p.city} ❓`}
                    </span>
                    <span className="font-round font-black" style={{ color: 'var(--pink)' }}>
                      <CountUp to={p.n} duration={900} />
                    </span>
                  </li>
                );
              })}
            </ol>
          )}
        </aside>
      </div>
    </PageShell>
  );
}
