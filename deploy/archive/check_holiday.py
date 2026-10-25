#!/usr/bin/env python3
"""验证节日特效截图:
- national-day: 有国旗红 #de2910 像素
- valentine: 有粉色系像素(#ff6b9d 附近)
- memorial: 页面大部分区域灰阶(饱和度极低)
"""
from PIL import Image
import os

SHOTS = r"D:\Agent_Work_Base\_shots"
P = F = 0


def ck(n, c, e=""):
    global P, F
    if c:
        print(f"PASS  {n}")
        P += 1
    else:
        print(f"FAIL  {n}  {e}")
        F += 1


def count_near(path, target, tol=25):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    n = 0
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            c = im.getpixel((x, y))
            if all(abs(a - b) <= tol for a, b in zip(c, target)):
                n += 1
    return n


def gray_ratio(path):
    """饱和度低的像素占比(公祭日全站黑白应接近 1)"""
    im = Image.open(path).convert("RGB")
    w, h = im.size
    gray = 0
    total = 0
    for y in range(0, h, 3):
        for x in range(0, w, 3):
            r, g, b = im.getpixel((x, y))
            total += 1
            mx, mn = max(r, g, b), min(r, g, b)
            if mx - mn < 18:   # 饱和度阈值
                gray += 1
    return gray / total


# 国旗红 #de2910 = (222, 41, 16)
n = count_near(os.path.join(SHOTS, "holiday_national-day.png"), (222, 41, 16), tol=30)
ck("国庆截图有国旗红", n > 40, f"n={n}")

# 爱心粉 #ff6b9d = (255, 107, 157) 附近(动画中的爱心是 emoji 渲染,颜色多样,放宽)
n = count_near(os.path.join(SHOTS, "holiday_valentine.png"), (255, 107, 157), tol=60)
ck("情人节截图有粉色系", n > 30, f"n={n}")

# 公祭日:饱和度极低的像素占比应 > 85%
g = gray_ratio(os.path.join(SHOTS, "holiday_memorial.png"))
ck("公祭日截图接近黑白", g > 0.85, f"gray={g:.2f}")

# 对照组:普通 about 页(浅色)灰度占比应明显低于公祭日
# 用刚才的假日截图里的 memorial 和常规截图比
g2 = gray_ratio(os.path.join(SHOTS, "holiday_valentine.png"))
ck("公祭日灰度 > 情人节灰度", g > g2, f"mem={g:.2f} val={g2:.2f}")

print()
print(f"通过 {P} 项,失败 {F} 项")
