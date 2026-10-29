"""把 TopoJSON 世界地图转成内嵌的 SVG path 数据。

为什么要预生成:
- 运行时拉 CDN 会引入外部依赖,国内网络还可能超时
- 预投影后直接是 SVG path,渲染零计算

投影:Natural Earth(d3.geoNaturalEarth1),等积折中,世界地图观感好。
城市点位在前端用同一套公式投影,保证经纬度与底图严格对齐。
"""
from __future__ import annotations

import json
import math
import urllib.request
from pathlib import Path

SRC = "https://unpkg.com/world-atlas@2/countries-110m.json"
OUT = Path("../frontend/src/lib/worldMap.ts")

# 视口:宽 1000,高由投影范围决定
VIEW_W = 1000


def natural_earth(lmbda_deg: float, phi_deg: float) -> tuple[float, float]:
    """d3.geoNaturalEarth1 的 raw 投影(弧度入,无量纲出)。"""
    lmbda = math.radians(lmbda_deg)
    phi = math.radians(phi_deg)
    phi2 = phi * phi
    phi4 = phi2 * phi2
    x = lmbda * (
        0.8707 - 0.131979 * phi2 + phi4 * (-0.013791 + phi4 * (0.003971 * phi2 - 0.001529 * phi4))
    )
    y = phi * (
        1.007226 + phi2 * (0.015085 + phi4 * (-0.044475 + 0.028874 * phi2 - 0.005916 * phi4))
    )
    return x, y


def decode_arcs(topo: dict) -> list[list[tuple[float, float]]]:
    """TopoJSON 的 arcs 是 delta 编码,还原成经纬度点列。"""
    transform = topo.get("transform")
    sx, sy = (transform["scale"] if transform else (1, 1))
    tx, ty = (transform["translate"] if transform else (0, 0))

    arcs = []
    for arc in topo["arcs"]:
        pts = []
        x = y = 0
        for dx, dy in arc:
            x += dx
            y += dy
            if transform:
                pts.append((x * sx + tx, y * sy + ty))
            else:
                pts.append((x, y))
        arcs.append(pts)
    return arcs


def ring_from_arcs(arc_indices: list[int], arcs: list[list[tuple[float, float]]]):
    """把若干 arc 拼成一个闭合环。负索引表示反向。"""
    ring: list[tuple[float, float]] = []
    for idx in arc_indices:
        if idx >= 0:
            seg = arcs[idx]
        else:
            seg = list(reversed(arcs[~idx]))
        if ring and seg:
            seg = seg[1:]  # 去掉重复的首点
        ring.extend(seg)
    return ring


def iter_polygons(geom: dict, arcs):
    """产出该 geometry 的所有外环(忽略内环/湖泊,110m 精度下够用)。"""
    gtype = geom.get("type")
    if gtype == "Polygon":
        for ring_idx in geom["arcs"]:
            yield ring_from_arcs(ring_idx, arcs)
    elif gtype == "MultiPolygon":
        for poly in geom["arcs"]:
            for ring_idx in poly:
                yield ring_from_arcs(ring_idx, arcs)


def main() -> None:
    print(f"下载 {SRC}")
    with urllib.request.urlopen(SRC, timeout=60) as r:
        topo = json.loads(r.read().decode("utf-8"))
    print(f"  大小: {len(json.dumps(topo)) / 1024:.0f} KB")

    arcs = decode_arcs(topo)
    print(f"  arcs: {len(arcs)}")

    # 先扫一遍所有点,求投影后的边界,用于归一化到视口
    xs, ys = [], []
    for arc in arcs:
        for lng, lat in arc:
            px, py = natural_earth(lng, lat)
            xs.append(px)
            ys.append(py)
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    spanx = maxx - minx
    scale = VIEW_W / spanx
    span_y = (maxy - miny) * scale
    VIEW_H = round(span_y)

    def project(lng: float, lat: float) -> tuple[float, float]:
        px, py = natural_earth(lng, lat)
        # Natural Earth 的 y 是数学坐标(北正南负),SVG 是屏幕坐标(南正北负),
        # 必须翻转,否则整张地图上下颠倒。
        return ((px - minx) * scale, (maxy - py) * scale)

    geometries = topo["objects"]["countries"]["geometries"]
    print(f"  国家/地区: {len(geometries)}")

    paths: list[str] = []
    total_pts = 0
    for geom in geometries:
        # 跳过南极洲(占版面又没访客)
        if geom.get("properties", {}).get("name") == "Antarctica":
            continue
        for ring in iter_polygons(geom, arcs):
            if len(ring) < 4:
                continue
            # 简化:点间距小于 0.4px 的点丢掉,大幅压体积且肉眼无差
            pts: list[tuple[float, float]] = []
            for lng, lat in ring:
                p = project(lng, lat)
                if pts and abs(p[0] - pts[-1][0]) < 0.4 and abs(p[1] - pts[-1][1]) < 0.4:
                    continue
                pts.append(p)
            if len(pts) < 3:
                continue
            total_pts += len(pts)
            d = "M" + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"
            paths.append(d)

    print(f"  路径段: {len(paths)}  总点数: {total_pts}")

    body = "\n".join(f"  '{p}'," for p in paths)
    ts = f'''/**
 * 世界地图轮廓数据(自动生成,勿手改)。
 *
 * 来源:world-atlas countries-110m(TopoJSON),经 Natural Earth 投影预计算。
 * 生成脚本:backend/scripts/gen_world_map.py
 *
 * 城市点位必须用同一个 project() 才能与底图对齐。
 */

export const MAP_VIEW = {{ width: {VIEW_W}, height: {VIEW_H} }};

/** 每个元素是一个国家的轮廓(已投影到 viewBox 坐标)。 */
export const WORLD_PATHS: string[] = [
{body}
];

// ---- 投影参数:与生成脚本一致 ----
const MIN_X = {minx!r};
const MAX_Y = {maxy!r};
const SCALE = {scale!r};

/** d3.geoNaturalEarth1 raw 投影 */
function naturalEarth(lambda: number, phi: number): [number, number] {{
  const phi2 = phi * phi;
  const phi4 = phi2 * phi2;
  const x =
    lambda *
    (0.8707 - 0.131979 * phi2 + phi4 * (-0.013791 + phi4 * (0.003971 * phi2 - 0.001529 * phi4)));
  const y =
    phi *
    (1.007226 + phi2 * (0.015085 + phi4 * (-0.044475 + 0.028874 * phi2 - 0.005916 * phi4)));
  return [x, y];
}}

/** 经纬度 -> 地图坐标(与底图同一投影) */
export function project(lng: number, lat: number): {{ x: number; y: number }} {{
  const [px, py] = naturalEarth((lng * Math.PI) / 180, (lat * Math.PI) / 180);
  return {{
    x: (px - MIN_X) * SCALE,
    // y 翻转:数学坐标(北正) -> 屏幕坐标(南正)
    y: (MAX_Y - py) * SCALE,
  }};
}}
'''
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(ts, encoding="utf-8", newline="\n")
    size_kb = OUT.stat().st_size / 1024
    print(f"\n✓ 写入 {OUT}  ({size_kb:.0f} KB, 视口 {VIEW_W}x{VIEW_H})")


if __name__ == "__main__":
    main()
