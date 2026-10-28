/**
 * 来访地图:等距圆柱投影 + 真实大陆轮廓 + 城市点位。
 *
 * 之前的实现只有一块纯色背景,点位落在空白画布上,看不出地理关系。
 * 这里用简化的大陆多边形(SVG path)做底图,再把城市按经纬度投影上去。
 *
 * 投影:等距圆柱(Plate Carrée),lng -180~180 → x 0~100%,lat 85~-60 → y 0~100%
 */
import { useMemo, useState } from 'react';
import { PageShell, Empty, ErrorBox, Loading } from '@/components/PageShell';
import { CountUp } from '@/components/CountUp';
import { useApi } from '@/lib/useApi';

interface CityPoint {
  city: string;
  n: number;
}

// 城市名 -> 经纬度。键用城市名最后一段(去掉省份前缀)
const CITY_COORDS: Record<string, [number, number]> = {
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
  唐山: [118.18, 39.63], 廊坊: [116.68, 39.52], 承德: [117.94, 40.98],
  保定: [115.46, 38.87], 秦皇岛: [119.60, 39.94], 邯郸: [114.49, 36.61],
  邢台: [114.51, 37.07], 沧州: [116.84, 38.30], 张家口: [114.89, 40.82],
  衡水: [115.67, 37.74], 定州: [114.99, 38.52], 辛集: [115.22, 37.94],
  Ashburn: [-77.49, 39.04], 馬納薩斯: [-77.47, 38.75], 曼萨萨斯: [-77.47, 38.75],
  東京: [139.69, 35.69], 东京: [139.69, 35.69], 大阪: [135.50, 34.69],
  首尔: [126.98, 37.57], 新加坡: [103.82, 1.35], 曼谷: [100.50, 13.75],
  伦敦: [-0.13, 51.51], 巴黎: [2.35, 48.86], 柏林: [13.40, 52.52],
  纽约: [-74.01, 40.71], 洛杉矶: [-118.24, 34.05], 旧金山: [-122.42, 37.77],
  西雅图: [-122.33, 47.61], 多伦多: [-79.38, 43.65], 悉尼: [151.21, -33.87],
};

// 极简大陆轮廓(SVG 1000x500 视口,经度 -180~180、纬度 90~-90 线性映射)
// 只求形状可辨认,不追求精度 —— 底图作用是给点位一个地理参照。
const CONTINENTS = [
  // 欧亚大陆
  'M 500 95 L 560 88 L 620 92 L 680 100 L 730 118 L 760 140 L 750 165 L 720 180 L 700 205 L 672 225 L 660 255 L 640 275 L 615 300 L 600 330 L 578 350 L 555 345 L 540 320 L 528 300 L 512 285 L 495 268 L 470 250 L 450 235 L 430 215 L 415 195 L 405 170 L 420 150 L 445 135 L 470 115 Z',
  // 非洲
  'M 505 300 L 535 295 L 560 310 L 575 340 L 585 375 L 578 410 L 560 440 L 535 455 L 512 445 L 495 420 L 485 390 L 480 360 L 488 330 Z',
  // 北美
  'M 150 110 L 215 100 L 270 108 L 300 125 L 315 150 L 305 175 L 285 190 L 270 215 L 250 235 L 235 265 L 220 285 L 205 275 L 195 250 L 180 230 L 165 205 L 150 180 L 140 150 Z',
  // 南美
  'M 265 290 L 300 285 L 320 305 L 330 340 L 325 380 L 310 415 L 295 440 L 280 430 L 272 400 L 265 365 L 258 330 Z',
  // 澳洲
  'M 790 355 L 835 350 L 862 365 L 870 390 L 855 412 L 825 420 L 798 408 L 782 385 Z',
  // 格陵兰
  'M 330 60 L 380 55 L 405 70 L 398 95 L 370 108 L 340 100 L 325 80 Z',
  // 南极(底边一条)
  'M 60 480 L 940 480 L 940 495 L 60 495 Z',
];

const W = 1000;
const H = 500;

/** 经纬度 -> SVG 坐标 */
function project(lng: number, lat: number): { x: number; y: number } {
  const x = ((lng + 180) / 360) * W;
  const y = ((90 - lat) / 180) * H;
  return { x, y };
}

/** 解析城市名:兼容「河北 石家庄」「美国 Ashburn」「日本」等格式 */
function resolveCoord(city: string): [number, number] | null {
  const parts = city.trim().split(/\s+/);
  // 从后往前找,优先匹配城市名
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

  // 能定位的点 vs 查不到坐标的点
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
        {/* 地图 */}
        <div className="lg:col-span-2">
          <div className="sticker overflow-hidden p-3">
            <svg
              viewBox={`0 0 ${W} ${H}`}
              className="w-full rounded-xl"
              style={{ background: 'var(--blue-bg)' }}
              role="img"
              aria-label="访客城市分布地图"
            >
              {/* 经纬网格 */}
              <g stroke="var(--rule)" strokeWidth="0.5" opacity="0.5">
                {[-120, -60, 0, 60, 120].map((lng) => {
                  const { x } = project(lng, 0);
                  return <line key={lng} x1={x} y1={0} x2={x} y2={H} />;
                })}
                {[-30, 0, 30, 60].map((lat) => {
                  const { y } = project(0, lat);
                  return <line key={lat} x1={0} y1={y} x2={W} y2={y} />;
                })}
              </g>

              {/* 大陆轮廓 */}
              <g
                fill="var(--teal-bg)"
                stroke="var(--teal)"
                strokeWidth="1.2"
                strokeLinejoin="round"
                opacity="0.9"
              >
                {CONTINENTS.map((d, i) => (
                  <path key={i} d={d} />
                ))}
              </g>

              {/* 城市点位 */}
              {placed.map((p) => {
                const r = 4 + (p.n / max) * 12;
                const active = hover === p.city;
                return (
                  <g
                    key={p.city}
                    onMouseEnter={() => setHover(p.city)}
                    onMouseLeave={() => setHover(null)}
                    style={{ cursor: 'pointer' }}
                  >
                    {/* 光晕 */}
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={r + 4}
                      fill="var(--pink)"
                      opacity={active ? 0.35 : 0.18}
                    />
                    <circle
                      cx={p.x}
                      cy={p.y}
                      r={r}
                      fill="var(--yellow)"
                      stroke="var(--shadow)"
                      strokeWidth="1.5"
                    />
                    {active && (
                      <g>
                        <rect
                          x={p.x + r + 6}
                          y={p.y - 20}
                          width={Math.max(80, p.city.length * 13 + 50)}
                          height="24"
                          rx="6"
                          fill="var(--paper)"
                          stroke="var(--shadow)"
                          strokeWidth="1.5"
                        />
                        <text
                          x={p.x + r + 12}
                          y={p.y - 4}
                          fontSize="13"
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
              圆点越大 = 访问越多{unplaced.length > 0 && ` · ${unplaced.length} 个城市未在坐标表中`}
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
