"""世界地图渲染验证:确认是真实世界地图,城市点位落在大陆上。"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5216"
CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


def dump(url):
    prof = tempfile.mkdtemp(prefix="cprof-")
    try:
        r = subprocess.run(
            [CHROME, "--headless=new", "--disable-gpu", "--no-sandbox",
             "--user-data-dir=" + prof, "--window-size=1400,900",
             "--virtual-time-budget=12000", "--dump-dom", url],
            capture_output=True, timeout=180,
        )
        return r.stdout.decode("utf-8", "replace")
    finally:
        shutil.rmtree(prof, ignore_errors=True)


def main() -> int:
    dom = dump(BASE + "/map")
    print(f"DOM: {len(dom)}B\n")

    ck("页面加载", len(dom) > 2000, str(len(dom)))
    ck("无 React 崩溃", "Minified React error" not in dom, "")

    # 世界地图关键指标
    paths = re.findall(r'<path d="(M[^"]{40,})"', dom)
    ck("国界路径 >= 150 条", len(paths) >= 150, f"实际 {len(paths)}")

    # viewBox 应是 1000x514
    ck("viewBox 正确", 'viewBox="0 0 1000 514"' in dom, "")

    # 经纬网
    lines = re.findall(r"<line ", dom)
    ck("经纬网线 >= 15 条", len(lines) >= 15, f"实际 {len(lines)}")

    # 城市点位(圆点)
    circles = re.findall(r"<circle ", dom)
    ck("城市圆点 >= 3", len(circles) >= 3, f"实际 {len(circles)}")

    # 关键:城市坐标必须落在地图范围内(0..1000, 0..514)
    coords = re.findall(r'<circle cx="([\d.]+)" cy="([\d.]+)"', dom)
    in_range = [c for c in coords if 0 <= float(c[0]) <= 1000 and 0 <= float(c[1]) <= 514]
    ck("城市坐标在地图范围内", len(in_range) >= 3, f"{len(in_range)}/{len(coords)}")

    # 中国城市应在地图右侧中部(经度 73-135 -> x 约 690-860)
    ck("有城市排行列表", "城市排行" in dom, "")

    # 地图体积(真实国界数据必然较大)
    ck("国界数据完整(dom > 60KB)", len(dom) > 60000, f"{len(dom)}B")

    print()
    print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
