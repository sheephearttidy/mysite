#!/usr/bin/env python3
"""渲染后台「前台特效」面板截图(静态模拟,用于视觉检查)"""
import io
import os
import re

ADMIN_HTML = r"D:\Agent_Work_Base\my-portfolio\admin\templates\admin.html"
ADMIN_CSS = r"D:\Agent_Work_Base\my-portfolio\admin\static\css\admin.css"
OUT = r"D:\Agent_Work_Base\_shots\_fx_panel.html"

with io.open(ADMIN_HTML, encoding="utf-8") as f:
    html = f.read()
with io.open(ADMIN_CSS, encoding="utf-8") as f:
    css = f.read()

# 抽 fx 面板
m = re.search(r'<section class="panel" id="panel-fx">.*?</section>', html, re.S)
panel = m.group(0).replace('class="panel"', 'class="panel active"', 1)

# 侧边栏分组(只留结构,去掉 Jinja)
sm = re.search(r'<nav class="sb-nav">.*?</nav>', html, re.S)
nav = sm.group(0) if sm else ""

doc = f"""<!doctype html>
<html lang="zh"><head><meta charset="utf-8">
<style>{css}</style>
<style>
body {{ margin:0; padding:24px; background:var(--bg); font-family:"ZCOOL KuaiLe",system-ui,sans-serif; }}
.demo {{ max-width:820px; }}
.sb-nav {{ background:var(--paper); padding:14px; border-radius:16px; border:3px solid var(--line); margin-bottom:24px; }}
</style></head>
<body>
<div class="demo">
  <h3 style="margin:0 0 12px">侧边栏分组(安全中心 + 前台特效)</h3>
  {nav}
  <h3 style="margin:24px 0 12px">前台特效面板</h3>
  {panel}
</div>
</body></html>"""

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
    f.write(doc)
print("写入", OUT, len(doc), "字符")
