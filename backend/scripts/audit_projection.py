"""验证世界地图投影正确性:用已知城市经纬度算坐标,检查地理关系。

关键检查(投影正确才成立):
- 东经城市 x 大于西经城市
- 南半球城市 y 大于北半球(屏幕坐标 y 向下)
- 相邻城市距离小
"""
import math
import re
import sys
from pathlib import Path

VIEW_W = 1000
VIEW_H = 514

src = Path(r"D:\Agent_ProJect\my-portfolio\frontend\src\lib\worldMap.ts").read_text(
    encoding="utf-8"
)
minx = float(re.search(r"const MIN_X = ([-\d.e]+);", src).group(1))
maxy = float(re.search(r"const MAX_Y = ([-\d.e]+);", src).group(1))
scale = float(re.search(r"const SCALE = ([-\d.e]+);", src).group(1))
print("参数: MIN_X=%.4f MAX_Y=%.4f SCALE=%.4f" % (minx, maxy, scale))
print()


def natural_earth(lmbda, phi):
    phi2 = phi * phi
    phi4 = phi2 * phi2
    x = lmbda * (
        0.8707 - 0.131979 * phi2 + phi4 * (-0.013791 + phi4 * (0.003971 * phi2 - 0.001529 * phi4))
    )
    y = phi * (
        1.007226 + phi2 * (0.015085 + phi4 * (-0.044475 + 0.028874 * phi2 - 0.005916 * phi4))
    )
    return x, y


def project(lng, lat):
    px, py = natural_earth(math.radians(lng), math.radians(lat))
    return (px - minx) * scale, (maxy - py) * scale


CITIES = {
    "伦敦": (-0.13, 51.51),
    "北京": (116.41, 39.90),
    "石家庄": (114.51, 38.04),
    "纽约": (-74.01, 40.71),
    "悉尼": (151.21, -33.87),
    "洛杉矶": (-118.24, 34.05),
    "东京": (139.69, 35.69),
    "新加坡": (103.82, 1.35),
}

pos = {}
print("%-10s %8s %7s %8s %8s" % ("城市", "经度", "纬度", "x", "y"))
for name, (lng, lat) in CITIES.items():
    x, y = project(lng, lat)
    pos[name] = (x, y)
    print("%-10s %8.2f %7.2f %8.1f %8.1f" % (name, lng, lat, x, y))

print()
PASS = FAIL = 0


def ck(name, cond, extra=""):
    global PASS, FAIL
    if cond:
        print("PASS  " + name)
        PASS += 1
    else:
        print("FAIL  " + name + "  " + extra)
        FAIL += 1


print("=== 地理关系校验 ===")
outside = [k for k, v in pos.items() if not (0 <= v[0] <= VIEW_W and 0 <= v[1] <= VIEW_H)]
ck("全部坐标在视口内", not outside, str(outside))

ck("北京 x > 伦敦 x(东经在西经右)", pos["北京"][0] > pos["伦敦"][0],
   "北京=%.0f 伦敦=%.0f" % (pos["北京"][0], pos["伦敦"][0]))
ck("伦敦 x > 纽约 x(西经更小)", pos["伦敦"][0] > pos["纽约"][0],
   "伦敦=%.0f 纽约=%.0f" % (pos["伦敦"][0], pos["纽约"][0]))
ck("东京 x > 北京 x(更东)", pos["东京"][0] > pos["北京"][0],
   "东京=%.0f 北京=%.0f" % (pos["东京"][0], pos["北京"][0]))

ck("悉尼 y > 北京 y(南半球靠下)", pos["悉尼"][1] > pos["北京"][1],
   "悉尼=%.0f 北京=%.0f" % (pos["悉尼"][1], pos["北京"][1]))
ck("新加坡 y > 北京 y(更南)", pos["新加坡"][1] > pos["北京"][1],
   "新加坡=%.0f 北京=%.0f" % (pos["新加坡"][1], pos["北京"][1]))
ck("北京 y > 伦敦 y(北京纬度更低)", pos["北京"][1] > pos["伦敦"][1],
   "北京=%.0f 伦敦=%.0f" % (pos["北京"][1], pos["伦敦"][1]))

d = math.dist(pos["北京"], pos["石家庄"])
ck("北京-石家庄距离 < 20px", d < 20, "%.1fpx" % d)

_, y0 = project(0, 0)
ck("赤道 y 在视口中部(200~320)", 200 <= y0 <= 320, "%.0f" % y0)

_, y_north = project(0, 80)
_, y_south = project(0, -60)
ck("北极 y 小于南极 y(上下不颠倒)", y_north < y_south,
   "北=%.0f 南=%.0f" % (y_north, y_south))

print()
print("通过 %d 项,失败 %d 项" % (PASS, FAIL))
sys.exit(1 if FAIL else 0)
