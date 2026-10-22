#!/usr/bin/env python3
"""生成 PWA 图标:粉底圆角 + 白色「杰」"""
from PIL import Image, ImageDraw, ImageFont

SIZE = 512
img = Image.new("RGB", (SIZE, SIZE), "#ff6b9d")
d = ImageDraw.Draw(img)

# 画一个白色圆角内框 + 简单赛车旗格纹装饰(呼应智能车)
inner = 40
d.rounded_rectangle([inner, inner, SIZE - inner, SIZE - inner],
                    radius=80, outline="#ffffff", width=16)
# 右下角小旗格
cell = 44
x0, y0 = SIZE - inner - 16 - cell * 3, SIZE - inner - 16 - cell * 2
for r in range(2):
    for c in range(3):
        if (r + c) % 2 == 0:
            d.rectangle([x0 + c * cell, y0 + r * cell,
                         x0 + (c + 1) * cell, y0 + (r + 1) * cell],
                        fill="#ffffff")

# 主字「杰」
font = None
for fp in [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc",
           r"C:\Windows\Fonts\simhei.ttf"]:
    try:
        font = ImageFont.truetype(fp, 260)
        break
    except OSError:
        continue
if font is None:
    font = ImageFont.load_default()
bbox = d.textbbox((0, 0), "杰", font=font)
w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
d.text(((SIZE - w) / 2 - bbox[0], (SIZE - h) / 2 - bbox[1] - 20),
       "杰", font=font, fill="#ffffff")

img.save(r"D:\Agent_Work_Base\my-portfolio\assets\icon-512.png")
img.resize((192, 192), Image.LANCZOS).save(
    r"D:\Agent_Work_Base\my-portfolio\assets\icon-192.png")
print("icons ok")
